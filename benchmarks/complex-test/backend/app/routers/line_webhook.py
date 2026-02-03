"""
LINE Webhook エンドポイント
"""
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any
from urllib.parse import parse_qs
from datetime import date

from app.db.database import get_db
from app.db.models import User, StressCheck, Company
from app.services.line_service import line_service
from app.services.ai_service import generate_counselor_response

router = APIRouter(prefix="/api/v1/line", tags=["line"])

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


@router.post("/webhook")
async def line_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """LINE Webhookエンドポイント"""
    # 署名検証
    signature = request.headers.get("X-Line-Signature", "")
    body = await request.body()

    if not line_service.verify_signature(body, signature):
        raise HTTPException(status_code=400, detail="Invalid signature")

    # イベント処理
    data = await request.json()
    events = data.get("events", [])

    for event in events:
        await handle_event(event, db)

    return {"status": "ok"}


async def handle_event(event: Dict[str, Any], db: AsyncSession):
    """イベントを処理"""
    event_type = event.get("type")

    if event_type == "message":
        await handle_message(event, db)
    elif event_type == "postback":
        await handle_postback(event, db)
    elif event_type == "follow":
        await handle_follow(event, db)


async def handle_follow(event: Dict[str, Any], db: AsyncSession):
    """友だち追加時の処理"""
    reply_token = event.get("replyToken")
    user_id = event["source"]["userId"]

    # プロフィール取得
    profile = await line_service.get_profile(user_id)
    display_name = profile.get("displayName", "ユーザー") if profile else "ユーザー"

    # ウェルカムメッセージ
    messages = [
        {
            "type": "text",
            "text": f"{display_name}さん、友だち追加ありがとうございます！\n\nこのアカウントでは、毎月のストレスチェックを簡単に行えます。\n\n会社から届く連携コードを入力してください。"
        }
    ]

    await line_service.reply_message(reply_token, messages)


async def handle_message(event: Dict[str, Any], db: AsyncSession):
    """メッセージイベントを処理"""
    reply_token = event.get("replyToken")
    user_id = event["source"]["userId"]
    message = event.get("message", {})

    if message.get("type") != "text":
        return

    text = message.get("text", "").strip()

    # 連携コード入力の処理
    if text.startswith("LINK:"):
        await handle_link_code(reply_token, user_id, text[5:], db)
        return

    # AI相談モード中の場合
    session = user_sessions.get(user_id, {})
    if session.get("mode") == "chat":
        await handle_chat_message(reply_token, user_id, text, db)
        return

    # デフォルト返信
    messages = [
        {
            "type": "text",
            "text": "ストレスチェックを開始するには、下のボタンをタップしてください。",
            "quickReply": {
                "items": [
                    {
                        "type": "action",
                        "action": {
                            "type": "postback",
                            "label": "📋 ストレスチェック",
                            "data": "action=start_stress_check"
                        }
                    },
                    {
                        "type": "action",
                        "action": {
                            "type": "postback",
                            "label": "💬 AIに相談",
                            "data": "action=start_chat"
                        }
                    }
                ]
            }
        }
    ]
    await line_service.reply_message(reply_token, messages)


async def handle_link_code(reply_token: str, line_user_id: str, code: str, db: AsyncSession):
    """連携コードを処理してユーザーをリンク"""
    # 連携コードでユーザーを検索
    result = await db.execute(
        select(User).where(User.link_code == code)
    )
    user = result.scalar_one_or_none()

    if not user:
        messages = [{"type": "text", "text": "連携コードが見つかりません。\n\n正しいコードを入力してください。\n例: LINK:ABC12345"}]
        await line_service.reply_message(reply_token, messages)
        return

    # 既に別のLINEアカウントと連携済みの場合
    if user.line_user_id and user.line_user_id != line_user_id:
        messages = [{"type": "text", "text": "このアカウントは既に別のLINEと連携されています。\n\n管理者にお問い合わせください。"}]
        await line_service.reply_message(reply_token, messages)
        return

    # LINE IDを保存
    user.link_code = None  # コードをクリア（使い捨て）
    user.line_user_id = line_user_id
    await db.commit()

    messages = [
        {
            "type": "text",
            "text": "✅ 連携が完了しました！\n\nこれからストレスチェックの通知がこちらに届きます。"
        }
    ]
    await line_service.reply_message(reply_token, messages)


async def handle_postback(event: Dict[str, Any], db: AsyncSession):
    """Postbackイベントを処理"""
    reply_token = event.get("replyToken")
    user_id = event["source"]["userId"]
    data = event.get("postback", {}).get("data", "")

    # データをパース
    params = parse_qs(data)
    action = params.get("action", [""])[0]

    if action == "start_stress_check":
        await start_stress_check(reply_token, user_id, db)
    elif action == "answer":
        q_num = int(params.get("q", [0])[0])
        score = int(params.get("score", [0])[0])
        await process_answer(reply_token, user_id, q_num, score, db)
    elif action == "start_chat":
        await start_chat_mode(reply_token, user_id)


async def start_stress_check(reply_token: str, user_id: str, db: AsyncSession):
    """ストレスチェックを開始"""
    # セッション初期化
    user_sessions[user_id] = {
        "mode": "stress_check",
        "current_question": 1,
        "answers": {}
    }

    # 最初の質問を送信
    messages = line_service.create_question_message(1, STRESS_QUESTIONS[0])
    await line_service.reply_message(reply_token, messages)


async def process_answer(reply_token: str, user_id: str, q_num: int, score: int, db: AsyncSession):
    """回答を処理"""
    session = user_sessions.get(user_id)

    if not session or session.get("mode") != "stress_check":
        messages = [{"type": "text", "text": "セッションが切れました。もう一度開始してください。"}]
        await line_service.reply_message(reply_token, messages)
        return

    # 回答を保存
    session["answers"][f"q{q_num}"] = score

    # 次の質問があるか確認
    next_q = q_num + 1
    if next_q <= len(STRESS_QUESTIONS):
        session["current_question"] = next_q
        messages = line_service.create_question_message(next_q, STRESS_QUESTIONS[next_q - 1])
        await line_service.reply_message(reply_token, messages)
    else:
        # 全質問完了 - 結果を保存
        await complete_stress_check(reply_token, user_id, session, db)


async def complete_stress_check(reply_token: str, user_id: str, session: Dict[str, Any], db: AsyncSession):
    """ストレスチェックを完了"""
    answers = session["answers"]
    total_score = sum(answers.values())

    # 高ストレス判定（例: 15点以上）
    is_high_stress = total_score >= 15

    # DBにユーザーがリンクされていれば保存
    result = await db.execute(
        select(User).where(User.line_user_id == user_id)
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
    messages = line_service.create_completion_message(is_high_stress)
    await line_service.reply_message(reply_token, messages)


async def start_chat_mode(reply_token: str, user_id: str):
    """AI相談モードを開始"""
    user_sessions[user_id] = {
        "mode": "chat",
        "history": []
    }

    messages = [
        {
            "type": "text",
            "text": "💬 AIカウンセラーです。\n\nお気軽にお話しください。何でも聞いています。\n\n（終了するには「終了」と入力してください）"
        }
    ]
    await line_service.reply_message(reply_token, messages)


async def handle_chat_message(reply_token: str, user_id: str, text: str, db: AsyncSession):
    """チャットメッセージを処理"""
    if text == "終了":
        user_sessions.pop(user_id, None)
        messages = [{"type": "text", "text": "相談を終了しました。またいつでもお話しください。"}]
        await line_service.reply_message(reply_token, messages)
        return

    # セッションから会話履歴を取得
    session = user_sessions.get(user_id, {"mode": "chat", "history": []})
    conversation_history = session.get("history", [])

    # OpenAI APIを使用してAI応答を生成
    ai_response = await generate_counselor_response(text, conversation_history)

    # 会話履歴を更新（セッションに保存）
    conversation_history.append({"role": "user", "content": text})
    conversation_history.append({"role": "assistant", "content": ai_response})

    # 履歴が長くなりすぎないように制限（最大20件）
    if len(conversation_history) > 20:
        conversation_history = conversation_history[-20:]

    session["history"] = conversation_history
    user_sessions[user_id] = session

    messages = [
        {
            "type": "text",
            "text": ai_response
        }
    ]
    await line_service.reply_message(reply_token, messages)


# ============================================
# 管理者向けAPI
# ============================================

@router.post("/send-stress-check")
async def send_stress_check_notification(
    company_id: str,
    db: AsyncSession = Depends(get_db)
):
    """会社全員にストレスチェック通知を送信"""
    # LINE連携済みユーザーを取得
    result = await db.execute(
        select(User).where(
            User.company_id == company_id,
            User.line_user_id.isnot(None)
        )
    )
    users = result.scalars().all()

    if not users:
        return {"status": "no_users", "count": 0}

    # メッセージを一斉送信
    user_ids = [u.line_user_id for u in users]
    messages = line_service.create_stress_check_start_message()

    success = await line_service.multicast_message(user_ids, messages)

    return {
        "status": "sent" if success else "failed",
        "count": len(user_ids)
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
            User.line_user_id.isnot(None)
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

    user_ids = [u.line_user_id for u in pending_users]
    messages = line_service.create_reminder_message()

    success = await line_service.multicast_message(user_ids, messages)

    return {
        "status": "sent" if success else "failed",
        "count": len(user_ids)
    }
