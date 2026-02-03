"""
Slack Webhook エンドポイント

Slack Events API と Interactivity のWebhookを処理します。
"""
from fastapi import APIRouter, Request, HTTPException, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any
from datetime import date
import json
import logging

from app.db.database import get_db
from app.db.models import User, StressCheck
from app.services.slack_service import slack_service
from app.services.ai_service import analyze_sentiment, generate_chat_reply

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/slack", tags=["slack"])

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


@router.post("/events")
async def slack_events(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Slack Events API エンドポイント

    メッセージイベントやアプリメンション等を受信します。
    """
    body = await request.body()
    timestamp = request.headers.get("X-Slack-Request-Timestamp", "")
    signature = request.headers.get("X-Slack-Signature", "")

    # 署名検証（本番環境では必須）
    if slack_service.signing_secret and not slack_service.verify_signature(body, timestamp, signature):
        raise HTTPException(status_code=400, detail="Invalid signature")

    data = await request.json()

    # URL検証チャレンジ（Slack App設定時に必要）
    if data.get("type") == "url_verification":
        return {"challenge": data.get("challenge")}

    # イベントコールバック処理
    if data.get("type") == "event_callback":
        event = data.get("event", {})
        # バックグラウンドで処理（3秒以内に応答するため）
        background_tasks.add_task(handle_event, event, db)

    return {"status": "ok"}


@router.post("/interactions")
async def slack_interactions(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Slack Interactivity エンドポイント

    ボタンクリック等のインタラクションを処理します。
    """
    body = await request.body()
    timestamp = request.headers.get("X-Slack-Request-Timestamp", "")
    signature = request.headers.get("X-Slack-Signature", "")

    # 署名検証
    if slack_service.signing_secret and not slack_service.verify_signature(body, timestamp, signature):
        raise HTTPException(status_code=400, detail="Invalid signature")

    # フォームデータをパース
    form_data = await request.form()
    payload_str = form_data.get("payload", "{}")
    payload = json.loads(payload_str)

    # バックグラウンドで処理
    background_tasks.add_task(handle_interaction, payload, db)

    # 即座に空の200応答を返す
    return {}


async def handle_event(event: Dict[str, Any], db: AsyncSession):
    """イベントを処理"""
    event_type = event.get("type")

    # Bot自身のメッセージは無視
    if event.get("bot_id"):
        return

    if event_type == "message":
        await handle_message_event(event, db)
    elif event_type == "app_mention":
        await handle_app_mention(event, db)


async def handle_message_event(event: Dict[str, Any], db: AsyncSession):
    """
    メッセージイベントを処理

    DMでのメッセージを受信した場合に応答します。
    """
    channel = event.get("channel", "")
    user_id = event.get("user", "")
    text = event.get("text", "").strip()
    channel_type = event.get("channel_type", "")

    if not text or not user_id:
        return

    # DMでのみ応答
    if channel_type != "im":
        return

    # チャットモード中の場合
    session = user_sessions.get(user_id, {})
    if session.get("mode") == "chat":
        await handle_chat_message(channel, user_id, text, db)
        return

    # ストレスチェック中の場合はボタンで回答するよう促す
    if session.get("mode") == "stress_check":
        await slack_service.post_message(
            channel=channel,
            text="上のボタンから回答を選択してください。"
        )
        return

    # 通常メッセージ - 挨拶を返す
    user_info = await slack_service.get_user_info(user_id)
    user_name = user_info.get("real_name", "ユーザー") if user_info else "ユーザー"

    greeting = slack_service.create_greeting_message(user_name)
    await slack_service.post_message(
        channel=channel,
        text=greeting["text"],
        blocks=greeting["blocks"]
    )


async def handle_app_mention(event: Dict[str, Any], db: AsyncSession):
    """アプリメンション（@Bot）を処理"""
    channel = event.get("channel", "")
    user_id = event.get("user", "")
    text = event.get("text", "").strip()
    thread_ts = event.get("thread_ts") or event.get("ts")

    # メンション部分を除去
    # 形式: <@BOTID> メッセージ
    import re
    clean_text = re.sub(r"<@[A-Z0-9]+>", "", text).strip()

    if not clean_text:
        # メンションのみの場合は挨拶
        user_info = await slack_service.get_user_info(user_id)
        user_name = user_info.get("real_name", "ユーザー") if user_info else "ユーザー"

        greeting = slack_service.create_greeting_message(user_name)
        await slack_service.post_message(
            channel=channel,
            text=greeting["text"],
            blocks=greeting["blocks"],
            thread_ts=thread_ts
        )
        return

    # AIチャット応答
    await handle_chat_message(channel, user_id, clean_text, db, thread_ts=thread_ts)


async def handle_interaction(payload: Dict[str, Any], db: AsyncSession):
    """インタラクション（ボタンクリック等）を処理"""
    action_type = payload.get("type")

    if action_type == "block_actions":
        actions = payload.get("actions", [])
        if actions:
            action = actions[0]
            action_id = action.get("action_id", "")
            value = action.get("value", "")
            user = payload.get("user", {})
            user_id = user.get("id", "")
            channel = payload.get("channel", {})
            channel_id = channel.get("id", "")
            message = payload.get("message", {})
            thread_ts = message.get("thread_ts") or message.get("ts")

            await handle_action(action_id, value, user_id, channel_id, db, thread_ts)


async def handle_action(
    action_id: str,
    value: str,
    user_id: str,
    channel_id: str,
    db: AsyncSession,
    thread_ts: str = None
):
    """アクションを処理"""

    if action_id == "start_stress_check":
        await start_stress_check(user_id, channel_id, thread_ts)

    elif action_id == "start_chat":
        await start_chat_mode(user_id, channel_id, thread_ts)

    elif action_id.startswith("stress_answer_"):
        # action_id形式: stress_answer_{q_num}_{score}
        parts = action_id.split("_")
        if len(parts) == 4:
            q_num = int(parts[2])
            score = int(parts[3])
            await process_stress_answer(user_id, channel_id, q_num, score, db, thread_ts)

    elif action_id.startswith("mood_"):
        mood = action_id.replace("mood_", "")
        await handle_mood_response(user_id, channel_id, mood, thread_ts)


async def start_stress_check(user_id: str, channel_id: str, thread_ts: str = None):
    """ストレスチェックを開始"""
    user_sessions[user_id] = {
        "mode": "stress_check",
        "current_question": 1,
        "answers": {},
        "channel_id": channel_id
    }

    question = slack_service.create_stress_check_question(1, STRESS_QUESTIONS[0])
    await slack_service.post_message(
        channel=channel_id,
        text=question["text"],
        blocks=question["blocks"],
        thread_ts=thread_ts
    )


async def process_stress_answer(
    user_id: str,
    channel_id: str,
    q_num: int,
    score: int,
    db: AsyncSession,
    thread_ts: str = None
):
    """ストレスチェックの回答を処理"""
    session = user_sessions.get(user_id)

    if not session or session.get("mode") != "stress_check":
        await slack_service.post_message(
            channel=channel_id,
            text="セッションが切れました。もう一度開始してください。",
            thread_ts=thread_ts
        )
        return

    # 回答を保存
    session["answers"][f"q{q_num}"] = score

    # 次の質問があるか確認
    next_q = q_num + 1
    if next_q <= len(STRESS_QUESTIONS):
        session["current_question"] = next_q
        question = slack_service.create_stress_check_question(next_q, STRESS_QUESTIONS[next_q - 1])
        await slack_service.post_message(
            channel=channel_id,
            text=question["text"],
            blocks=question["blocks"],
            thread_ts=thread_ts
        )
    else:
        # 全質問完了 - 結果を保存
        await complete_stress_check(user_id, channel_id, session, db, thread_ts)


async def complete_stress_check(
    user_id: str,
    channel_id: str,
    session: Dict[str, Any],
    db: AsyncSession,
    thread_ts: str = None
):
    """ストレスチェックを完了"""
    answers = session["answers"]
    total_score = sum(answers.values())

    # 高ストレス判定（例: 15点以上）
    is_high_stress = total_score >= 15

    # DBにユーザーがリンクされていれば保存
    result = await db.execute(
        select(User).where(User.slack_id == user_id)
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
    result_msg = slack_service.create_stress_check_result(is_high_stress, total_score)
    await slack_service.post_message(
        channel=channel_id,
        text=result_msg["text"],
        blocks=result_msg["blocks"],
        thread_ts=thread_ts
    )


async def start_chat_mode(user_id: str, channel_id: str, thread_ts: str = None):
    """AI相談モードを開始"""
    user_sessions[user_id] = {
        "mode": "chat",
        "history": [],
        "channel_id": channel_id
    }

    await slack_service.post_message(
        channel=channel_id,
        text="AIカウンセラーです。お気軽にお話しください。終了するには「終了」と入力してください。",
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": ":speech_balloon: *AIカウンセラーです*\n\nお気軽にお話しください。何でも聞いています。\n\n（終了するには「終了」と入力してください）"
                }
            }
        ],
        thread_ts=thread_ts
    )


async def handle_chat_message(
    channel_id: str,
    user_id: str,
    text: str,
    db: AsyncSession,
    thread_ts: str = None
):
    """チャットメッセージを処理してAI応答を返す"""
    if text == "終了":
        user_sessions.pop(user_id, None)
        await slack_service.post_message(
            channel=channel_id,
            text="相談を終了しました。またいつでもお話しください。",
            thread_ts=thread_ts
        )
        return

    # AI応答を生成
    try:
        reply = await generate_chat_reply(text)
    except Exception as e:
        logger.error(f"AI応答生成エラー: {e}")
        reply = "お話しいただきありがとうございます。もう少し詳しく聞かせていただけますか？"

    response_msg = slack_service.create_ai_response_message(reply)
    await slack_service.post_message(
        channel=channel_id,
        text=response_msg["text"],
        blocks=response_msg["blocks"],
        thread_ts=thread_ts
    )


async def handle_mood_response(user_id: str, channel_id: str, mood: str, thread_ts: str = None):
    """調子の回答を処理"""
    responses = {
        "good": "調子が良いようですね！:sparkles: その調子で頑張ってください。",
        "normal": "普通ですか。何かあればいつでもお話しください。:slightly_smiling_face:",
        "tired": "お疲れ様です。:hugging_face: 無理せずに、休息も大切にしてくださいね。\n\nもしよければ、AIカウンセラーに相談することもできます。"
    }

    text = responses.get(mood, "回答ありがとうございます。")

    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": text
            }
        }
    ]

    # 疲れている場合は相談ボタンを表示
    if mood == "tired":
        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "AIに相談する"},
                    "style": "primary",
                    "action_id": "start_chat",
                    "value": "start"
                }
            ]
        })

    await slack_service.post_message(
        channel=channel_id,
        text=text,
        blocks=blocks,
        thread_ts=thread_ts
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
    # Slack連携済みユーザーを取得
    result = await db.execute(
        select(User).where(
            User.company_id == company_id,
            User.slack_id.isnot(None)
        )
    )
    users = result.scalars().all()

    if not users:
        return {"status": "no_users", "count": 0}

    success_count = 0
    casual_msg = slack_service.create_casual_check_message()

    for user in users:
        # DMチャンネルを開いてメッセージ送信
        dm_channel = await slack_service.open_dm(user.slack_id)
        if dm_channel:
            result = await slack_service.post_message(
                channel=dm_channel,
                text=casual_msg["text"],
                blocks=casual_msg["blocks"]
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
            User.slack_id.isnot(None)
        )
    )
    users = result.scalars().all()

    if not users:
        return {"status": "no_users", "count": 0}

    success_count = 0

    for user in users:
        dm_channel = await slack_service.open_dm(user.slack_id)
        if dm_channel:
            # ストレスチェック開始を促すメッセージ
            result = await slack_service.post_message(
                channel=dm_channel,
                text="ストレスチェックのお知らせ",
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": ":clipboard: *今月のストレスチェックの時間です*\n\n5つの質問に答えてください（約1分）"
                        }
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {"type": "plain_text", "text": "開始する"},
                                "style": "primary",
                                "action_id": "start_stress_check",
                                "value": "start"
                            }
                        ]
                    }
                ]
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
            User.slack_id.isnot(None)
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

    for user in pending_users:
        dm_channel = await slack_service.open_dm(user.slack_id)
        if dm_channel:
            result = await slack_service.post_message(
                channel=dm_channel,
                text="ストレスチェックリマインダー",
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": ":bell: *ストレスチェックがまだ完了していません*\n\n下のボタンから回答をお願いします。"
                        }
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {"type": "plain_text", "text": "回答する"},
                                "style": "primary",
                                "action_id": "start_stress_check",
                                "value": "start"
                            }
                        ]
                    }
                ]
            )
            if result:
                success_count += 1

    return {
        "status": "sent",
        "count": success_count,
        "total": len(pending_users)
    }
