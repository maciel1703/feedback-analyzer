import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from . import nlp
from .db import Base, Feedback, engine, get_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="Feedback Analyzer", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


class FeedbackIn(BaseModel):
    text: str = Field(min_length=3, max_length=5000)
    source: str = "manual"


class BulkIn(BaseModel):
    texts: list[str] = Field(min_length=1, max_length=500)
    source: str = "bulk"


def serialize(f: Feedback) -> dict:
    return {
        "id": f.id, "text": f.text, "source": f.source,
        "sentiment": f.sentiment, "score": f.score, "created_at": f.created_at.isoformat(),
    }


def analyze_and_save(db: Session, texts: list[str], source: str) -> list[Feedback]:
    texts = [t.strip() for t in texts if t and len(t.strip()) >= 3]
    if not texts:
        raise HTTPException(422, "Nenhum comentário válido para analisar.")
    rows = [
        Feedback(text=t, source=source, sentiment=label, score=score)
        for t, (label, score) in zip(texts, nlp.classify(texts))
    ]
    db.add_all(rows)
    db.commit()
    for r in rows:
        db.refresh(r)
    return rows


@app.post("/api/feedbacks", status_code=201)
def create_feedback(body: FeedbackIn, db: Session = Depends(get_db)):
    return serialize(analyze_and_save(db, [body.text], body.source)[0])


@app.post("/api/feedbacks/bulk", status_code=201)
def create_bulk(body: BulkIn, db: Session = Depends(get_db)):
    return [serialize(r) for r in analyze_and_save(db, body.texts, body.source)]


@app.get("/api/feedbacks")
def list_feedbacks(limit: int = 30, sentiment: str | None = None, db: Session = Depends(get_db)):
    q = select(Feedback).order_by(Feedback.created_at.desc()).limit(min(limit, 200))
    if sentiment:
        q = q.where(Feedback.sentiment == sentiment)
    return [serialize(f) for f in db.scalars(q)]


@app.delete("/api/feedbacks", status_code=204)
def clear_feedbacks(db: Session = Depends(get_db)):
    db.execute(delete(Feedback))
    db.commit()


@app.get("/api/summary")
def summary(db: Session = Depends(get_db)):
    counts = dict(db.execute(select(Feedback.sentiment, func.count()).group_by(Feedback.sentiment)).all())
    counts = {k: counts.get(k, 0) for k in ("positive", "neutral", "negative")}
    day = func.date_trunc("day", Feedback.created_at)
    trend: dict[str, dict] = {}
    for d, s, c in db.execute(
        select(day, Feedback.sentiment, func.count()).group_by(day, Feedback.sentiment).order_by(day)
    ):
        key = d.date().isoformat()
        trend.setdefault(key, {"date": key, "positive": 0, "neutral": 0, "negative": 0})[s] = c
    return {
        "total": sum(counts.values()),
        "counts": counts,
        "avg_score": round(db.scalar(select(func.avg(Feedback.score))) or 0, 3),
        "trend": list(trend.values()),
    }


@app.get("/api/topics")
def topics(n: int = 5, db: Session = Depends(get_db)):
    rows = db.execute(select(Feedback.text, Feedback.sentiment)).all()
    return nlp.extract_topics([r[0] for r in rows], [r[1] for r in rows], n_topics=min(max(n, 1), 10))
