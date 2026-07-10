from pydantic import BaseModel
from typing import Optional


class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None


class QueryResponse(BaseModel):
    session_id: str
    answer: Optional[str] = None
    status: str
    last_observation: Optional[str] = None
    last_error: Optional[str] = None