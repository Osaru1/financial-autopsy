# Financial Autopsy

A small first version: load transactions, see where the money went, find monthly charges, and ask a question about the month.

The screen talks to a FastAPI backend. The backend does the math. A model, when you add an API key, only explains that summary.

## Run the API

PostgreSQL has to be running first. With Docker:

```bash
docker compose up -d
```

The backend expects this connection string, which matches the compose file:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

## Run the screen

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000 and load the sample transactions.

A CSV import uses the columns `date,merchant,amount,category`. Spending amounts are negative.

## Ask with a model

Set `LLM_API_KEY` in `backend/.env`. Any OpenAI-compatible chat API works. `LLM_BASE_URL` and `LLM_MODEL` choose the provider. Without a key, answers are still calculated from the same summary.
