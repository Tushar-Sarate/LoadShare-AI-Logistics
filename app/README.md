# LoadShare AI Logistics

A food and parcel delivery platform with an AI support assistant. Customers order food from restaurants, an admin assigns a delivery partner, the partner delivers, and the customer tracks the order live. An AI chatbot answers policy questions and looks up the user's own orders.

## Features
- Three roles: customer, delivery partner, admin (JWT auth, role-based access)
- Restaurants, menus, cart, bill and food orders
- Partner assignment by pincode (row locking prevents double assignment)
- Order status flow: Pending, Assigned, Picked Up, In Transit, Delivered (steps cannot be skipped)
- Tracking history for every order
- Simulated payments (UPI, Card, Cash on Delivery) and complaints
- Role-based screens: customer app, partner job feed, admin control room

## AI layer
- **RAG:** policy documents, MiniLM embeddings, ChromaDB
- **LangGraph workflow:** classifies each question and routes it to RAG, order tools or complaint handling
- **Tool calling:** order status and tracking, restricted to the logged-in user's own orders (the user comes from the JWT, never from the LLM)
- **Guardrails:** prompt-injection filter, ownership check on order lookups, answers only from retrieved context
- **Observability:** one JSON log line per chat (user, intent, latency, blocked or not) in `logs/chatbot.log`
- **LLM:** Groq (Llama)

## Evaluation
Keyword-based scoring on a small hand-written test set.

| Metric | Result |
|---|---|
| Retrieval hit rate (chunk size 400 / 800 / 1200) | 100% / 100% / 100% |
| Answer accuracy (20 questions) | 100% |
| Out-of-scope refusal (3 questions) | 3/3 |
| Intent routing (8 questions) | 100% |

The first run scored 80% because my keyword matcher was too strict (formatting differences, not wrong answers). I fixed the matcher, not the chatbot.

**Limitations:** the test set is small and written from the same documents, so high scores are expected. Chunk size made no difference because the documents are short. Next steps: a larger and harder test set and LLM-as-judge scoring.

Run it:
```
uv run python -m evaluation.rag_eval
```

## Tech stack
FastAPI, PostgreSQL, SQLAlchemy, LangChain, LangGraph, ChromaDB, Groq, HTML/CSS/JavaScript, pytest, Docker

## Project structure
```
app/
  models/     database tables
  schemas/    request and response rules
  routers/    API endpoints
  services/   business logic (charge, assignment, tracking)
  security/   JWT, passwords, role checks
  ai/         llm, prompts, tools, guardrails, rag/, langchain/, langgraph/
documents/    policy files used by RAG
evaluation/   RAG evaluation script
frontend/     website (HTML, CSS, JS)
tests/        automated tests
```

## Run locally
1. Create a PostgreSQL database named `loadshare_db`.
2. Create a `.env` file:
```
DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/loadshare_db
SECRET_KEY=your_long_random_secret
GROQ_API_KEY=your_groq_key
```
3. Run:
```
uv sync
uv run python reset_db.py
uv run python create_admin.py
uv run python seed_food.py
uv run python -m app.ai.rag.vectorstore
uv run uvicorn app.main:app --reload
```
4. Open http://127.0.0.1:8000/site/index.html (API docs at http://127.0.0.1:8000/docs).

Admin login: `admin@loadshare.com` (password is set in `create_admin.py`).

## Demo flow
1. Sign up as a delivery partner and save the profile (pincode 411040).
2. Sign up as a customer, save the profile, open a restaurant, add items, place the order.
3. Log in as admin and click **Assign partner**.
4. Log in as the partner and press the three buttons: picked up, out for delivery, delivered.
5. The customer sees the progress bar and tracking history, and can pay and ask the chatbot.

## Tests
```
uv run pytest -v
```
20 tests covering auth, orders, tracking, partners, AI guardrails and order ownership.

## Run with Docker
```
docker compose up --build
docker compose exec api python create_admin.py
docker compose exec api python seed_food.py
```

## Known limitations
- Payments are simulated (no real gateway)
- Partner assignment is by pincode, not real distance or GPS
- Order screens refresh every 10 seconds (no push updates)
- Notifications are a placeholder
- Database tables are created with `create_all` (no Alembic migrations)

## Screenshots
Add images here: restaurants, cart and bill, order tracking, admin panel, chatbot guardrails.