from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(os.getenv("MONGODB_URI"))
db = client["research_agent"]

sessions_collection = db["sessions"]
cache_collection = db["tool_cache"]
reports_collection = db["reports"]

def save_session(session_id: str, messages: list) -> None:
    sessions_collection.update_one(
        {"session_id": session_id},
        {
            "$set": {
                "session_id": session_id,
                "messages": messages,
                "updated_at": datetime.utcnow()
            },
            "$setOnInsert": {
                "created_at": datetime.utcnow()
            }
        },
        upsert=True
    )


def load_session(session_id: str) -> list:
    session = sessions_collection.find_one({"session_id": session_id})
    if session:
        return session["messages"]
    return []