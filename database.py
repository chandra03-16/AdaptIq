"""
MongoDB connection and collection accessors.
Uses Motor (async MongoDB driver) for FastAPI compatibility.
"""

import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "adaptive_engine")

client: AsyncIOMotorClient = None


async def connect_db():
    global client
    client = AsyncIOMotorClient(MONGO_URI)
    print(f"[DB] Connected to MongoDB at {MONGO_URI}")


async def close_db():
    global client
    if client:
        client.close()
        print("[DB] MongoDB connection closed")


def get_db():
    return client[DB_NAME]


def get_questions_col():
    return get_db()["questions"]


def get_sessions_col():
    return get_db()["user_sessions"]
