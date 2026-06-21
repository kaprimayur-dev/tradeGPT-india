# TradeGPT India Architecture

## Frontend

* Next.js
* Tailwind CSS
* ShadCN UI
* Plotly Charts

Responsibilities:

* Chat UI
* Stock Dashboard
* Portfolio Dashboard
* Backtesting Dashboard

---

## Backend

FastAPI

Responsibilities:

* API endpoints
* Agent orchestration
* Data fetching
* RAG execution

---

## AI Layer

LLM:

* Gemini

Framework:

* LangGraph

Agents:

1. Router Agent
2. Research Agent
3. Fundamental Agent
4. Technical Agent
5. Portfolio Agent
6. Strategy Agent
7. Report Agent

---

## RAG Layer

Documents:

* Annual Reports
* Earnings Calls
* SEBI Documents
* RBI Reports

Pipeline:

PDF → Chunking → Embedding → ChromaDB → Retrieval → Gemini

---

## Databases

### PostgreSQL

Stores:

* Users
* Portfolios
* Queries

### ChromaDB

Stores:

* Document embeddings
* Metadata
