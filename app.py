from pydantic import BaseModel
from typing import Optional
from fastapi import FastAPI
from agent_core import run_react_loop
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None


class QueryResponse(BaseModel):
    session_id: str
    answer: Optional[str] = None
    status: str
    last_observation: Optional[str] = None
    last_error: Optional[str] = None

@app.post("/query",response_model=QueryRequest)

def query_agent(request:QueryRequest):
    result = run_react_loop(query=request.query, session_id=request.session_id)