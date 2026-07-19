# AI Research Agent V1 (Built From Scratch)

<!-- Add a hero image or demo GIF here showing the agent answering a query -->
<!-- ![Demo](./assets/demo.gif) -->

## 1. Overview

A from-scratch implementation of a **ReAct (Reasoning + Acting) AI agent** that answers research questions by autonomously deciding when to search the web, when to perform calculations, and when it has enough information to give a final answer. Built without any agent framework (no LangChain, no LangGraph) — the entire reasoning loop, tool-calling logic, and persistence layer are hand-written to demonstrate a first-principles understanding of how autonomous LLM agents actually work under the hood.

Wrapped in a production-style FastAPI backend with MongoDB-backed session memory, this project served as the foundation for a more advanced LangGraph-based iteration ([V2](https://github.com/Sk-husamuddin/Research-Agent-Project-v2)), built for the **InnoGenesis 2026** Agentic AI hackathon.

## 2. Motivation

Most tutorials teach agent-building by wiring together framework abstractions (LangChain agents, pre-built tool classes) without ever explaining what's actually happening inside the loop. This project was built to answer a simple question: **what does an LLM agent actually do, mechanically, at every step?**

By hand-writing the ReAct loop, tool dispatch, and session persistence from scratch, this project demonstrates a genuine understanding of agent internals — the same understanding that later made it possible to rebuild the same logic on LangGraph (V2) deliberately and correctly, rather than just following framework conventions.

## 3. Features

- **ReAct reasoning loop** — the agent alternates between reasoning (deciding what to do) and acting (calling a tool), iterating until it has a final answer
- **Two working tools**: real-time web search (Tavily API) and safe mathematical calculation (asteval, no `eval()`)
- **Persistent conversation memory** — MongoDB-backed sessions, so follow-up questions ("double that number") correctly reference earlier answers
- **Tool result caching** — repeated queries skip redundant external API calls, reducing cost and latency
- **Multi-provider LLM support** — switchable between Groq (Llama 3.1) and GitHub Models (GPT-4.1-mini)
- **FastAPI REST API** — a clean `/query` endpoint, with Pydantic request/response validation and proper error handling
- **Research report history** — every completed research task is saved permanently and independently retrievable

## 4. Architecture

```
┌─────────────┐      HTTP POST /query      ┌──────────────┐
│   Client     │ ─────────────────────────▶ │   FastAPI     │
│ (curl/UI)    │ ◀───────────────────────── │   (app.py)    │
└─────────────┘        JSON response        └──────┬───────┘
                                                     │
                                                     ▼
                                          ┌────────────────────┐
                                          │  run_react_loop()   │
                                          │  (agent_core.py)    │
                                          └─────────┬──────────┘
                                                     │
                       ┌─────────────────────────────┼─────────────────────────────┐
                       ▼                             ▼                             ▼
              ┌─────────────────┐          ┌──────────────────┐          ┌──────────────────┐
              │   LLM Provider   │          │   Tool Registry   │          │     MongoDB       │
              │ (Groq / GitHub)  │          │ search_web        │          │ sessions          │
              │                  │          │ calculate          │          │ tool_cache        │
              └─────────────────┘          └──────────────────┘          │ reports            │
                                                                          └──────────────────┘
```

## 5. How It Works

1. A user sends a query to `POST /query` with an optional `session_id`.
2. If `session_id` is new, a fresh conversation begins with a system prompt establishing the agent's rules. If it's an existing session, prior conversation history is loaded from MongoDB.
3. The agent enters its **ReAct loop**: it calls the LLM with the current conversation and available tools.
4. If the LLM requests a tool call (`search_web` or `calculate`), the agent executes it, caches the result, appends it to the conversation, and loops back to the LLM — now armed with real data.
5. Once the LLM produces a final answer (no further tool calls requested), the loop exits, the conversation and a research report are saved to MongoDB, and the answer is returned to the client.

## 6. Tech Stack

| Layer | Technology |
|---|---|
| Language | Python |
| Web Framework | FastAPI |
| LLM Providers | Groq (Llama 3.1), GitHub Models (GPT-4.1-mini) |
| Web Search | Tavily API |
| Math Evaluation | asteval (safe expression evaluation, no `eval()`) |
| Database | MongoDB Atlas |
| Validation | Pydantic |

## 7. Folder Structure

```
Research-Agent-Project/
├── main.py              # Standalone terminal ReAct agent (reference implementation)
├── agent_core.py         # Core ReAct loop, extracted as a reusable function
├── app.py                 # FastAPI wrapper — /query endpoint
├── database/
│   └── mongo.py           # MongoDB sessions, tool cache, and reports
├── .env.example            # Environment variable template
└── requirements.txt
```

## 8. Installation

```bash
git clone https://github.com/Sk-husamuddin/Research-Agent-Project.git
cd Research-Agent-Project
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file with:
```
GROQ_API_KEY=your_key_here
TAVILY_API_KEY=your_key_here
MONGODB_URI=your_mongodb_connection_string
GITHUB_TOKEN=your_github_models_token
```

Run the API:
```bash
uvicorn app:app --reload
```

Visit `http://127.0.0.1:8000/docs` for interactive API documentation (Swagger UI).

## 9. API Endpoints

### `POST /query`

**Request:**
```json
{
  "query": "What is the population of India?",
  "session_id": null
}
```

**Response:**
```json
{
  "session_id": "generated-or-reused-uuid",
  "answer": "The current population of India is approximately...",
  "status": "success"
}
```

Reuse the returned `session_id` in subsequent requests to continue the same conversation with full context.

## 10. Agent Workflow

The agent follows the classic **ReAct (Reason + Act)** pattern:

```
User Query
    │
    ▼
Call LLM ──────────────┐
    │                   │
    ▼                   │
Tool call requested?    │
    │                   │
   Yes ──▶ Execute Tool ─┘  (loop back to LLM with tool result)
    │
   No
    │
    ▼
Return Final Answer
```

## 11. Memory System (MongoDB)

Three collections provide persistence:

- **`sessions`** — full conversation history per `session_id`, enabling multi-turn context (e.g., resolving "double that number" using an earlier tool result)
- **`tool_cache`** — normalized query/expression → result mappings, with a 24-hour TTL index, avoiding redundant Tavily/calculation calls across all users
- **`reports`** — a permanent, append-only log of every completed research task, independently queryable by session

## 12. Tools

| Tool | Purpose | Underlying implementation |
|---|---|---|
| `search_web` | Real-time information retrieval | Tavily Search API |
| `calculate` | Safe mathematical evaluation | asteval `Interpreter` (sandboxed, no `eval()`) |

Both tools are wrapped with caching handlers that check for a previously computed result before making a real external call.

## 13. Demo

### Example: Multi-step Research Query

**Request & Response:**

<img width="800" alt="Query request and response" src="https://github.com/user-attachments/assets/7aaa5dec-c587-441c-a1cb-b0d56e9b40ff" />

### Example: Follow-up Question (Session Continuity)

The agent correctly resolves "double that number" using the population figure from the previous turn, confirming MongoDB session memory works across requests.

<img width="800" alt="Follow-up query showing session continuity" src="https://github.com/user-attachments/assets/43f4e005-2717-47af-a045-7b139714a1d7" />

### MongoDB Persistence

Sessions and reports are saved as real documents in MongoDB Atlas, confirming persistence works beyond just the in-memory request/response cycle.

<img width="800" alt="MongoDB Sessions and Reports collections" src="https://github.com/user-attachments/assets/4dbf8074-f75e-4208-9ddb-1e889ce31b86" />


## 14. Future Improvements

- Context window truncation for very long conversations (currently sends full history every call)
- Multi-user session listing (currently sessions are only retrievable by exact `session_id`)
- Streaming responses for real-time "thinking" visibility
- See [V2](#) for the LangGraph-based evolution of this project, including planner-based multi-step reasoning and MCP tool integration

## 15. Learnings

Building this from scratch (rather than starting with a framework) surfaced several non-obvious lessons:
- The entire "memory" of an LLM agent is just the conversation history re-sent on every call — there is no other mechanism
- Tool result caching requires careful normalization; naive string matching only catches exact-phrasing repeats, not semantically identical queries
- Separating orchestration (`agent_core.py`) from transport (`app.py`) makes it trivial to swap FastAPI for another framework later without touching agent logic

## 16. License

MIT
