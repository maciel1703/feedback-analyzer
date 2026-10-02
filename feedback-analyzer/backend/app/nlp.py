"""NLP: classificação de sentimento (Transformers) e tópicos recorrentes (TF-IDF + NMF)."""
import os
from collections import Counter
from functools import lru_cache

from sklearn.decomposition import NMF
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer

MODEL = os.getenv("SENTIMENT_MODEL", "cardiffnlp/twitter-xlm-roberta-base-sentiment")

_LABELS = {
    "label_0": "negative", "label_1": "neutral", "label_2": "positive",
    "negative": "negative", "neutral": "neutral", "positive": "positive",
}

STOPWORDS = set(ENGLISH_STOP_WORDS) | set(
    """a o as os um uma uns umas de do da dos das em no na nos nas por para com sem sob sobre
    ao aos à às e ou mas que se como mais menos muito muita muitos muitas pouco já também ainda
    só até então quando onde porque pois é são foi era ser estar está estão estou estava tem têm
    tinha ter teve há havia fazer faz fez isso isto esse essa esses essas este esta estes estas
    aquele aquela eu tu ele ela nós vocês eles elas meu minha meus minhas seu sua seus suas me te
    lhe lhes nem num numa pelo pela pelos pelas qual quais cada tudo todo toda todos todas outro
    outra outros outras bem mal vez vezes sempre nunca coisa coisas pra pro tá aí aqui lá""".split()
)


@lru_cache(maxsize=1)
def _pipeline():
    from transformers import pipeline  # import tardio: o modelo só é baixado/carregado no 1º uso

    return pipeline("text-classification", model=MODEL, top_k=None, truncation=True, max_length=256)


def classify(texts: list[str]) -> list[tuple[str, float]]:
    """Retorna [(rótulo, score)] onde score = P(positivo) - P(negativo)."""
    results = []
    for probs in _pipeline()(texts, batch_size=16):
        p = {_LABELS.get(r["label"].lower(), r["label"].lower()): r["score"] for r in probs}
        label = max(p, key=p.get)
        results.append((label, round(p.get("positive", 0) - p.get("negative", 0), 4)))
    return results


def extract_topics(texts, sentiments, n_topics=5, n_terms=6):
    """Agrupa os comentários em tópicos (NMF sobre TF-IDF) e soma o sentimento de cada um."""
    if len(texts) < 6:
        return []
    vec = TfidfVectorizer(
        stop_words=sorted(STOPWORDS),
        ngram_range=(1, 2),
        max_df=0.85,
        min_df=2 if len(texts) >= 30 else 1,
        token_pattern=r"(?u)\b[^\W\d_]{3,}\b",
    )
    try:
        X = vec.fit_transform(texts)
    except ValueError:  # vocabulário vazio
        return []

    k = max(1, min(n_topics, len(texts) // 4, X.shape[1]))
    nmf = NMF(n_components=k, init="nndsvda", random_state=42, max_iter=500)
    W = nmf.fit_transform(X)
    terms = vec.get_feature_names_out()
    assign = W.argmax(axis=1)

    topics = []
    for i, comp in enumerate(nmf.components_):
        top = [str(terms[j]) for j in comp.argsort()[::-1][:n_terms]]
        idx = [d for d, a in enumerate(assign) if a == i and W[d].sum() > 0]
        if not idx:
            continue
        dist = Counter(sentiments[d] for d in idx)
        topics.append({
            "id": i,
            "label": ", ".join(top[:3]),
            "terms": top,
            "count": len(idx),
            "sentiment": {s: dist.get(s, 0) for s in ("positive", "neutral", "negative")},
        })
    return sorted(topics, key=lambda t: -t["count"])
