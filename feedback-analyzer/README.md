# Analisador de feedback do cliente

Classifica o sentimento de comentários (Transformers, pt-BR incluído), identifica tópicos
recorrentes (TF-IDF + NMF com scikit-learn), guarda tudo em PostgreSQL e exibe em um painel React.

```
feedback-analyzer/
├── docker-compose.yml        # PostgreSQL 16
├── backend/                  # FastAPI + SQLAlchemy + NLP
│   ├── app/{main,db,nlp}.py
│   ├── seed.py               # comentários de exemplo
│   ├── requirements.txt
│   └── .env.example
└── frontend/                 # React + Vite + Recharts
```

## Requisitos
Python 3.10+, Node 18+, Docker (ou um PostgreSQL local).

## 1. Banco de dados
```bash
docker compose up -d
```
Sem Docker: crie o usuário e o banco `feedback` (senha `feedback`) no seu PostgreSQL
ou ajuste `DATABASE_URL` no `.env`. As tabelas são criadas automaticamente na primeira execução.

## 2. Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```
Na primeira análise o modelo de sentimento (~1 GB) é baixado e fica em cache; a primeira
requisição demora mais. Documentação interativa em http://localhost:8000/docs.

Dados de exemplo (opcional, com o banco no ar): `python seed.py`

## 3. Frontend
```bash
cd frontend
npm install
npm run dev
```
Abra http://localhost:5173 (o Vite encaminha `/api` para `localhost:8000`).

## API
| Método | Rota | Descrição |
|---|---|---|
| POST | `/api/feedbacks` | `{text, source?}` analisa e salva um comentário |
| POST | `/api/feedbacks/bulk` | `{texts: [...]}` analisa e salva vários |
| GET | `/api/feedbacks?limit=&sentiment=` | lista os mais recentes |
| GET | `/api/summary` | totais, nota média e tendência por dia |
| GET | `/api/topics?n=5` | tópicos recorrentes com sentimento de cada um |
| DELETE | `/api/feedbacks` | apaga tudo |

## Ajustes
- **Outro modelo:** `SENTIMENT_MODEL` no `.env` (precisa de rótulos negative/neutral/positive).
- **Tópicos ruins:** adicione palavras genéricas do seu negócio em `STOPWORDS` (`nlp.py`) ou mude `n`.
- **Produção:** restrinja `CORS_ORIGINS`, use migrações (Alembic) e mova a análise para uma fila
  se o volume crescer.
