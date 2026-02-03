"""
Discord Webhook エンドポイント

Discord Interactions APIのWebhookを処理します。
"""
from fastapi import APIRouter, Request, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any
from datetime import date
import logging

from app.db.database import get_db
from app.db.models import User, StressCheck
from app.services.discord_service import discord_service
from app.services.ai_service import generate_chat_reply

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/discord", tags=["discord"])

# ストレスチェックの質問（簡易版5問）
STRESS_QUESTIONS = [
    "最近、仕事で強いストレスを感じていますか？",
    "十分な睡眠が取れていますか？",
    "仕事に対するやりがいを感じていますか？",
    "職場の人間関係は良好ですか？",
    "体調の不調（頭痛、肩こり等）はありますか？",
]

# ユーザーごとの回答状態を一時保存（本番ではRedis推奨）
user_sessions: Dict[str, Dict[str, Any]] = {}


@router.post("/interactions")
async def discord_interactions(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Discord Interactions API エンドポイント

    スラッシュコマンド、ボタンクリック等のインタラクションを受信します。
    """
    body = await request.body()
    signature = request.headers.get("X-Signature-Ed25519", "")
    timestamp = request.headers.get("X-Signature-Timestamp", "")

    # 署名検証
    if discord_service.public_key and not discord_service.verify_signature(body, signature, timestamp):
        raise HTTPException(status_code=401, detail="Invalid signature")

    data = await request.json()
    interaction_type = data.get("type")

    # PING検証（Discord App設定時に必要）
    if interaction_type == 1:
        return JSONResponse(content={"type": 1})

    # APPLICATION_COMMAND（スラッシュコマンド）
    if interaction_type == 2:
        return await handle_application_command(data, db)

    # MESSAGE_COMPONENT（ボタン等）
    if interaction_type == 3:
        return await handle_message_component(data, background_tasks, db)

    return JSONResponse(content={"type": 1})


async def handle_application_command(data: Dict[str, Any], db: AsyncSession) -> JSONResponse:
    """スラッシュコマンドを処理"""
    command_name = data.get("data", {}).get("name", "")
    user = data.get("member", {}).get("user", {}) or data.get("user", {})
    user_id = user.get("id", "")
    user_name = user.get("username", "ユーザー")

    if command_name == "stress_check":
        # ストレスチェック開始
        user_sessions[user_id] = {
            "mode": "stress_check",
            "current_question": 1,
            "answers": {}
        }
        question = discord_service.create_stress_check_question_embed(1, STRESS_QUESTIONS[0])
        return JSONResponse(content={
            "type": 4,  # CHANNEL_MESSAGE_WITH_SOURCE
            "data": {
                "embeds": question["embeds"],
                "components": question["components"],
                "flags": 64  # EPHEMERAL（本人のみ表示）
            }
        })

    elif command_name == "chat":
        # AI相談モード開始
        user_sessions[user_id] = {
            "mode": "chat",
            "history": []
        }
        return JSONResponse(content={
            "type": 4,
            "data": {
                "embeds": [
                    {
                        "title": "💬 AIカウンセラーです",
                        "description": "お気軽にお話しください。何でも聞いています。\n\n（終了するには「終了」と入力してください）",
                        "color": 0x5865F2
                    }
                ],
                "flags": 64
            }
        })

    elif command_name == "help":
        # ヘルプ
        greeting = discord_service.create_greeting_embed(user_name)
        return JSONResponse(content={
            "type": 4,
            "data": {
                "embeds": greeting["embeds"],
                "components": greeting["components"],
                "flags": 64
            }
        })

    # 不明なコマンド
    return JSONResponse(content={
        "type": 4,
        "data": {
            "content": "不明なコマンドです。`/help` でヘルプを表示できます。",
            "flags": 64
        }
    })


async def handle_message_component(
    data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db: AsyncSession
) -> JSONResponse:
    """メッセージコンポーネント（ボタン等）のインタラクションを処理"""
    custom_id = data.get("data", {}).get("custom_id", "")
    user = data.get("member", {}).get("user", {}) or data.get("user", {})
    user_id = user.get("id", "")
    interaction_id = data.get("id", "")
    interaction_token = data.get("token", "")

    if custom_id == "start_stress_check":
        return await start_stress_check(user_id)

    elif custom_id == "start_chat":
        return await start_chat_mode(user_id)

    elif custom_id.startswith("stress_answer_"):
        # custom_id形式: stress_answer_{q_num}_{score}
        parts = custom_id.split("_")
        if len(parts) == 4:
            q_num = int(parts[2])
            score = int(parts[3])
            return await process_stress_answer(user_id, q_num, score, db)

    elif custom_id.startswith("mood_"):
        mood = custom_id.replace("mood_", "")
        return await handle_mood_response(user_id, mood)

    # 不明なアクション
    return JSONResponse(content={
        "type": 4,
        "data": {
            "content": "セッションが切れました。もう一度開始してください。",
            "flags": 64
        }
    })


async def start_stress_check(user_id: str) -> JSONResponse:
    """ストレスチェックを開始"""
    user_sessions[user_id] = {
        "mode": "stress_check",
        "current_question": 1,
        "answers": {}
    }

    question = discord_service.create_stress_check_question_embed(1, STRESS_QUESTIONS[0])
    return JSONResponse(content={
        "type": 4,
        "data": {
            "embeds": question["embeds"],
            "components": question["components"],
            "flags": 64
        }
    })


async def process_stress_answer(
    user_id: str,
    q_num: int,
    score: int,
    db: AsyncSession
) -> JSONResponse:
    """ストレスチェックの回答を処理"""
    session = user_sessions.get(user_id)

    if not session or session.get("mode") != "stress_check":
        return JSONResponse(content={
            "type": 4,
            "data": {
                "content": "セッションが切れました。もう一度開始してください。",
                "flags": 64
            }
        })

    # 回答を保存
    session["answers"][f"q{q_num}"] = score

    # 次の質問があるか確認
    next_q = q_num + 1
    if next_q <= len(STRESS_QUESTIONS):
        session["current_question"] = next_q
        question = discord_service.create_stress_check_question_embed(next_q, STRESS_QUESTIONS[next_q - 1])
        return JSONResponse(content={
            "type": 4,
            "data": {
                "embeds": question["embeds"],
                "components": question["components"],
                "flags": 64
            }
        })
    else:
        # 全質問完了 - 結果を保存
        return await complete_stress_check(user_id, session, db)


async def complete_stress_check(
    user_id: str,
    session: Dict[str, Any],
    db: AsyncSession
) -> JSONResponse:
    """ストレスチェックを完了"""
    answers = session["answers"]
    total_score = sum(answers.values())

    # 高ストレス判定（例: 15点以上）
    is_high_stress = total_score >= 15

    # DBにユーザーがリンクされていれば保存
    result = await db.execute(
        select(User).where(User.discord_id == user_id)
    )
    user = result.scalar_one_or_none()

    if user:
        stress_check = StressCheck(
            user_id=user.id,
            period=date.today().replace(day=1),
            answers=answers,
            total_score=total_score,
            is_high_stress=is_high_stress
        )
        db.add(stress_check)
        await db.commit()

    # セッションクリア
    user_sessions.pop(user_id, None)

    # 完了メッセージ
    result_msg = discord_service.create_stress_check_result_embed(is_high_stress, total_score)
    return JSONResponse(content={
        "type": 4,
        "data": {
            "embeds": result_msg["embeds"],
            "components": result_msg.get("components", []),
            "flags": 64
        }
    })


async def start_chat_mode(user_id: str) -> JSONResponse:
    """AI相談モードを開始"""
    user_sessions[user_id] = {
        "mode": "chat",
        "history": []
    }

    return JSONResponse(content={
        "type": 4,
        "data": {
            "embeds": [
                {
                    "title": "💬 AIカウンセラーです",
                    "description": "お気軽にお話しください。何でも聞いています。\n\n（終了するには「終了」と入力してください）",
                    "color": 0x5865F2
                }
            ],
            "flags": 64
        }
    })


async def handle_mood_response(user_id: str, mood: str) -> JSONResponse:
    """調子の回答を処理"""
    responses = {
        "good": ("調子が良いようですね！✨ その調子で頑張ってください。", 0x57F287),
        "normal": ("普通ですか。何かあればいつでもお話しください。🙂", 0x5865F2),
        "tired": ("お疲れ様です。🤗 無理せずに、休息も大切にしてくださいね。", 0xFEE75C)
    }

    text, color = responses.get(mood, ("回答ありがとうございます。", 0x5865F2))

    response_data: Dict[str, Any] = {
        "embeds": [
            {
                "description": text,
                "color": color
            }
        ],
        "flags": 64
    }

    # 疲れている場合は相談ボタンを表示
    if mood == "tired":
        response_data["components"] = [
            {
                "type": 1,
                "components": [
                    {
                        "type": 2,
                        "style": 1,
                        "label": "AIに相談する",
                        "custom_id": "start_chat"
                    }
                ]
            }
        ]

    return JSONResponse(content={
        "type": 4,
        "data": response_data
    })


# ============================================
# Gateway Bot用イベントハンドラ（オプション）
# ============================================

@router.post("/message")
async def handle_message_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    メッセージイベント処理（Gateway Bot使用時）

    Discord Gateway経由でメッセージを受信した際に呼び出されます。
    """
    data = await request.json()
    content = data.get("content", "").strip()
    user_id = data.get("author", {}).get("id", "")
    channel_id = data.get("channel_id", "")

    if not content or not user_id:
        return {"status": "ignored"}

    # Bot自身のメッセージは無視
    if data.get("author", {}).get("bot"):
        return {"status": "ignored"}

    # チャットモード中の場合
    session = user_sessions.get(user_id, {})
    if session.get("mode") == "chat":
        background_tasks.add_task(handle_chat_message, channel_id, user_id, content)
        return {"status": "processing"}

    return {"status": "ok"}


async def handle_chat_message(channel_id: str, user_id: str, text: str):
    """チャットメッセージを処理してAI応答を返す"""
    if text == "終了":
        user_sessions.pop(user_id, None)
        await discord_service.send_message(
            channel_id=channel_id,
            content="相談を終了しました。またいつでもお話しください。"
        )
        return

    # AI応答を生成
    try:
        reply = await generate_chat_reply(text)
    except Exception as e:
        logger.error(f"AI応答生成エラー: {e}")
        reply = "お話しいただきありがとうございます。もう少し詳しく聞かせていただけますか？"

    response_msg = discord_service.create_ai_response_embed(reply)
    await discord_service.send_message(
        channel_id=channel_id,
        content="",
        embeds=response_msg["embeds"]
    )


# ============================================
# 管理者向けAPI
# ============================================

@router.post("/send-casual-check")
async def send_casual_check(
    company_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    会社全員にカジュアルな問いかけを送信

    「調子はどう？」等のカジュアルなメッセージを送信します。
    """
    # Discord連携済みユーザーを取得
    result = await db.execute(
        select(User).where(
            User.company_id == company_id,
            User.discord_id.isnot(None)
        )
    )
    users = result.scalars().all()

    if not users:
        return {"status": "no_users", "count": 0}

    success_count = 0
    casual_msg = discord_service.create_casual_check_embed()

    for user in users:
        result = await discord_service.send_dm(
            user_id=user.discord_id,
            content="",
            embeds=casual_msg["embeds"],
            components=casual_msg["components"]
        )
        if result:
            success_count += 1

    return {
        "status": "sent",
        "count": success_count,
        "total": len(users)
    }


@router.post("/send-stress-check")
async def send_stress_check_notification(
    company_id: str,
    db: AsyncSession = Depends(get_db)
):
    """会社全員にストレスチェック通知を送信"""
    result = await db.execute(
        select(User).where(
            User.company_id == company_id,
            User.discord_id.isnot(None)
        )
    )
    users = result.scalars().all()

    if not users:
        return {"status": "no_users", "count": 0}

    success_count = 0
    notification = discord_service.create_stress_check_notification_embed()

    for user in users:
        result = await discord_service.send_dm(
            user_id=user.discord_id,
            content="",
            embeds=notification["embeds"],
            components=notification["components"]
        )
        if result:
            success_count += 1

    return {
        "status": "sent",
        "count": success_count,
        "total": len(users)
    }


@router.post("/send-reminder")
async def send_reminder(
    company_id: str,
    db: AsyncSession = Depends(get_db)
):
    """未回答者にリマインダーを送信"""
    current_period = date.today().replace(day=1)

    # 今月未回答のユーザーを取得
    result = await db.execute(
        select(User).where(
            User.company_id == company_id,
            User.discord_id.isnot(None)
        )
    )
    users = result.scalars().all()

    # 回答済みユーザーを除外
    pending_users = []
    for user in users:
        check_result = await db.execute(
            select(StressCheck).where(
                StressCheck.user_id == user.id,
                StressCheck.period == current_period
            )
        )
        if not check_result.scalar_one_or_none():
            pending_users.append(user)

    if not pending_users:
        return {"status": "all_completed", "count": 0}

    success_count = 0
    reminder = discord_service.create_reminder_embed()

    for user in pending_users:
        result = await discord_service.send_dm(
            user_id=user.discord_id,
            content="",
            embeds=reminder["embeds"],
            components=reminder["components"]
        )
        if result:
            success_count += 1

    return {
        "status": "sent",
        "count": success_count,
        "total": len(pending_users)
    }
