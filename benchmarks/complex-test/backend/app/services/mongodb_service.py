"""
MongoDB接続設定とチャット履歴サービス
"""
import os
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from bson import ObjectId
from dotenv import load_dotenv

load_dotenv()

# MongoDB接続設定
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "stressagent")

# グローバルMongoDBクライアント
_client: Optional[AsyncIOMotorClient] = None
_db: Optional[AsyncIOMotorDatabase] = None


async def get_mongodb_client() -> AsyncIOMotorClient:
    """MongoDBクライアントを取得"""
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(MONGODB_URL)
    return _client


async def get_mongodb() -> AsyncIOMotorDatabase:
    """MongoDBデータベースを取得"""
    global _db
    if _db is None:
        client = await get_mongodb_client()
        _db = client[MONGODB_DB_NAME]
        # インデックス作成
        await _db.chat_history.create_index([("user_id", 1), ("created_at", -1)])
    return _db


async def close_mongodb():
    """MongoDB接続を閉じる"""
    global _client, _db
    if _client is not None:
        _client.close()
        _client = None
        _db = None


# チャット履歴コレクションのスキーマ
# {
#     "_id": ObjectId,
#     "user_id": str (UUID),
#     "role": "user" | "ai",
#     "content": str,
#     "sentiment_score": float (optional, AI応答の場合),
#     "created_at": datetime
# }


async def save_chat_message(
    user_id: UUID,
    role: str,
    content: str,
    sentiment_score: Optional[float] = None
) -> str:
    """
    チャットメッセージをMongoDBに保存

    Args:
        user_id: ユーザーID
        role: メッセージの役割 ("user" または "ai")
        content: メッセージ内容
        sentiment_score: 感情スコア (AI応答の場合のみ)

    Returns:
        保存されたドキュメントのID
    """
    db = await get_mongodb()

    document = {
        "user_id": str(user_id),
        "role": role,
        "content": content,
        "created_at": datetime.utcnow()
    }

    if sentiment_score is not None:
        document["sentiment_score"] = sentiment_score

    result = await db.chat_history.insert_one(document)
    return str(result.inserted_id)


async def get_chat_history(
    user_id: UUID,
    limit: int = 50,
    offset: int = 0
) -> List[dict]:
    """
    ユーザーのチャット履歴を取得

    Args:
        user_id: ユーザーID
        limit: 取得する最大件数
        offset: スキップする件数

    Returns:
        チャットメッセージのリスト
    """
    db = await get_mongodb()

    cursor = db.chat_history.find(
        {"user_id": str(user_id)}
    ).sort("created_at", 1).skip(offset).limit(limit)

    messages = []
    async for doc in cursor:
        message = {
            "id": str(doc["_id"]),
            "role": doc["role"],
            "content": doc["content"],
            "created_at": doc["created_at"].isoformat()
        }
        if "sentiment_score" in doc:
            message["sentiment_score"] = doc["sentiment_score"]
        messages.append(message)

    return messages


async def get_chat_history_count(user_id: UUID) -> int:
    """
    ユーザーのチャット履歴の総数を取得

    Args:
        user_id: ユーザーID

    Returns:
        チャット履歴の総数
    """
    db = await get_mongodb()
    count = await db.chat_history.count_documents({"user_id": str(user_id)})
    return count


async def delete_chat_history(user_id: UUID) -> int:
    """
    ユーザーのチャット履歴を全削除

    Args:
        user_id: ユーザーID

    Returns:
        削除されたドキュメント数
    """
    db = await get_mongodb()
    result = await db.chat_history.delete_many({"user_id": str(user_id)})
    return result.deleted_count


async def delete_chat_message(user_id: UUID, message_id: str) -> bool:
    """
    特定のチャットメッセージを削除

    Args:
        user_id: ユーザーID
        message_id: メッセージID

    Returns:
        削除成功の場合True
    """
    db = await get_mongodb()
    result = await db.chat_history.delete_one({
        "_id": ObjectId(message_id),
        "user_id": str(user_id)
    })
    return result.deleted_count > 0
