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

cache_collection.create_index("timestamp",expireAfterSeconds=86400)

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

def get_cached_result(tool_name: str, query: str) -> str | None:
    cache = cache_collection.find_one({
        "tool_name": tool_name,
        "query": query
    })
    
    if cache:
        age = datetime.now(timezone.utc) - cache["timestamp"]
        if age.total_seconds() < 86400:  # 86400 = 24 hours in seconds
            return cache["result"]
    
    return None


def save_cached_result(tool_name: str, query: str, result: str) -> None:
    cache_collection.update_one(
        {"tool_name": tool_name, "query": query},
        {
            "$set": {
                "tool_name": tool_name,
                "query": query,
                "result": result,
                "timestamp": datetime.utcnow()
            }
        },
        upsert=True
    )

def save_report(session_id: str, topic: str, report: str) -> None:
    reports_collection.insert_one({
        "session_id": session_id,
        "topic": topic,
        "report": report,
        "generated_at": datetime.now(timezone.utc)
    })


def get_reports(session_id: str) -> list:
    reports = reports_collection.find(
        {"session_id": session_id},
        {"_id": 0}
    ).sort("generated_at", -1)
    return list(reports)