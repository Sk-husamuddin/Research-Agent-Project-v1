import os
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime, timezone

load_dotenv()

uri = os.getenv("MONGODB_URI")
print("URI:", uri)

client = MongoClient(uri)
db = client["research_agent"]

# Try inserting directly into Atlas
result = db["sessions"].insert_one({
    "test": "atlas_connection_test",
    "timestamp": datetime.now(timezone.utc)
})

print("Inserted ID:", result.inserted_id)

# Count documents
count = db["sessions"].count_documents({})
print("Total sessions in Atlas:", count)