"""
Slack Bot API連携サービス

Slack Events API / Web APIを使用してBotメッセージを処理します。
"""
import os
import hmac
import hashlib
import time
from typing import Optional, List, Dict, Any
import httpx
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET", "")
SLACK_API_BASE = "https://slack.com/api"


class SlackService:
    """Slack Bot API操作クラス"""

    def __init__(self):
        self.bot_token = SLACK_BOT_TOKEN
        self.signing_secret = SLACK_SIGNING_SECRET
        self.headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {self.bot_token}"
        }

    def verify_signature(self, body: bytes, timestamp: str, signature: str) -> bool:
        """
        Slack Webhookの署名を検証

        Args:
            body: リクエストボディ
            timestamp: X-Slack-Request-Timestamp ヘッダー
            signature: X-Slack-Signature ヘッダー

        Returns:
            署名が有効な場合True
        """
        if not self.signing_secret:
            logger.warning("SLACK_SIGNING_SECRET が設定されていません")
            return False

        # タイムスタンプの検証（5分以内）
        try:
            request_time = int(timestamp)
            if abs(time.time() - request_time) > 60 * 5:
                logger.warning("リクエストのタイムスタンプが古すぎます")
                return False
        except ValueError:
            return False

        # 署名の検証
        sig_basestring = f"v0:{timestamp}:{body.decode('utf-8')}"
        expected_signature = "v0=" + hmac.new(
            self.signing_secret.encode("utf-8"),
            sig_basestring.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(signature, expected_signature)

    async def post_message(
        self,
        channel: str,
        text: str,
        blocks: Optional[List[Dict[str, Any]]] = None,
        thread_ts: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        チャンネルにメッセージを送信

        Args:
            channel: チャンネルID または ユーザーID（DM用）
            text: メッセージテキスト（フォールバック用）
            blocks: Block Kit形式のメッセージ
            thread_ts: スレッドに返信する場合のタイムスタンプ

        Returns:
            APIレスポンス or None（失敗時）
        """
        if not self.bot_token:
            logger.warning("SLACK_BOT_TOKEN が設定されていません")
            return None

        payload: Dict[str, Any] = {
            "channel": channel,
            "text": text
        }
        if blocks:
            payload["blocks"] = blocks
        if thread_ts:
            payload["thread_ts"] = thread_ts

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{SLACK_API_BASE}/chat.postMessage",
                    headers=self.headers,
                    json=payload
                )
                result = response.json()
                if not result.get("ok"):
                    logger.error(f"Slackメッセージ送信エラー: {result.get('error')}")
                    return None
                return result
            except Exception as e:
                logger.error(f"Slack API呼び出しエラー: {e}")
                return None

    async def open_dm(self, user_id: str) -> Optional[str]:
        """
        ユーザーとのDMチャンネルを開く

        Args:
            user_id: SlackユーザーID

        Returns:
            DMチャンネルID or None
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{SLACK_API_BASE}/conversations.open",
                    headers=self.headers,
                    json={"users": user_id}
                )
                result = response.json()
                if result.get("ok"):
                    return result.get("channel", {}).get("id")
                logger.error(f"DM開設エラー: {result.get('error')}")
                return None
            except Exception as e:
                logger.error(f"Slack API呼び出しエラー: {e}")
                return None

    async def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        ユーザー情報を取得

        Args:
            user_id: SlackユーザーID

        Returns:
            ユーザー情報 or None
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{SLACK_API_BASE}/users.info",
                    headers=self.headers,
                    params={"user": user_id}
                )
                result = response.json()
                if result.get("ok"):
                    return result.get("user")
                return None
            except Exception as e:
                logger.error(f"ユーザー情報取得エラー: {e}")
                return None

    async def send_ephemeral(
        self,
        channel: str,
        user_id: str,
        text: str,
        blocks: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        エフェメラルメッセージ（本人のみに見える）を送信

        Args:
            channel: チャンネルID
            user_id: 対象ユーザーID
            text: メッセージテキスト
            blocks: Block Kit形式のメッセージ

        Returns:
            成功時True
        """
        payload: Dict[str, Any] = {
            "channel": channel,
            "user": user_id,
            "text": text
        }
        if blocks:
            payload["blocks"] = blocks

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{SLACK_API_BASE}/chat.postEphemeral",
                    headers=self.headers,
                    json=payload
                )
                result = response.json()
                return result.get("ok", False)
            except Exception as e:
                logger.error(f"エフェメラルメッセージ送信エラー: {e}")
                return False

    # ============================================
    # メッセージテンプレート
    # ============================================

    def create_greeting_message(self, user_name: str) -> Dict[str, Any]:
        """挨拶メッセージを作成"""
        return {
            "text": f"{user_name}さん、こんにちは！",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*{user_name}さん、こんにちは！* :wave:\n\n私はメンタルヘルスサポートBotです。お気軽にお話しください。"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "ストレスチェック開始"
                            },
                            "style": "primary",
                            "action_id": "start_stress_check",
                            "value": "start"
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "AIに相談"
                            },
                            "action_id": "start_chat",
                            "value": "start"
                        }
                    ]
                }
            ]
        }

    def create_casual_check_message(self) -> Dict[str, Any]:
        """カジュアルな問いかけメッセージを作成"""
        return {
            "text": "調子はどうですか？",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": ":sunny: *調子はどうですか？*\n\n今日の調子を教えてください。何かあればお気軽にお話しください。"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "元気"
                            },
                            "style": "primary",
                            "action_id": "mood_good",
                            "value": "good"
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "普通"
                            },
                            "action_id": "mood_normal",
                            "value": "normal"
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "ちょっと疲れた"
                            },
                            "style": "danger",
                            "action_id": "mood_tired",
                            "value": "tired"
                        }
                    ]
                }
            ]
        }

    def create_stress_check_question(self, question_num: int, question_text: str) -> Dict[str, Any]:
        """ストレスチェック質問メッセージを作成"""
        return {
            "text": f"Q{question_num}. {question_text}",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Q{question_num}.* {question_text}"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "全くない"},
                            "action_id": f"stress_answer_{question_num}_1",
                            "value": "1"
                        },
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "少しある"},
                            "action_id": f"stress_answer_{question_num}_2",
                            "value": "2"
                        },
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "ある程度"},
                            "action_id": f"stress_answer_{question_num}_3",
                            "value": "3"
                        },
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "かなりある"},
                            "style": "danger",
                            "action_id": f"stress_answer_{question_num}_4",
                            "value": "4"
                        }
                    ]
                }
            ]
        }

    def create_stress_check_result(self, is_high_stress: bool, total_score: int) -> Dict[str, Any]:
        """ストレスチェック結果メッセージを作成"""
        if is_high_stress:
            return {
                "text": "ストレスチェック完了 - 高ストレス傾向",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": ":white_check_mark: *ストレスチェックが完了しました*"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f":warning: ストレスが高めの傾向があります（スコア: {total_score}）\n\n無理せず、必要であればAIカウンセラーに相談してください。"
                        }
                    },
                    {
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
                    }
                ]
            }
        else:
            return {
                "text": "ストレスチェック完了",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": ":white_check_mark: *ストレスチェックが完了しました*"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f":sparkles: 現在のストレスレベルは正常範囲内です（スコア: {total_score}）\n\n引き続き健康管理にお気をつけください！"
                        }
                    }
                ]
            }

    def create_ai_response_message(self, reply: str) -> Dict[str, Any]:
        """AI応答メッセージを作成"""
        return {
            "text": reply,
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": reply
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": ":robot_face: AIカウンセラーからの返信"
                        }
                    ]
                }
            ]
        }


# シングルトンインスタンス
slack_service = SlackService()
