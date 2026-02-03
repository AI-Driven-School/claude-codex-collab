"""
LINE Messaging API連携サービス
"""
import os
import hashlib
import hmac
import base64
from typing import Optional, List, Dict, Any
import httpx
from dotenv import load_dotenv

load_dotenv()

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
LINE_API_BASE = "https://api.line.me/v2/bot"


class LineService:
    """LINE Messaging API操作クラス"""

    def __init__(self):
        self.access_token = LINE_CHANNEL_ACCESS_TOKEN
        self.channel_secret = LINE_CHANNEL_SECRET
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token}"
        }

    def verify_signature(self, body: bytes, signature: str) -> bool:
        """Webhookの署名を検証"""
        hash = hmac.new(
            self.channel_secret.encode("utf-8"),
            body,
            hashlib.sha256
        ).digest()
        expected_signature = base64.b64encode(hash).decode("utf-8")
        return hmac.compare_digest(signature, expected_signature)

    async def reply_message(self, reply_token: str, messages: List[Dict[str, Any]]) -> bool:
        """メッセージを返信"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{LINE_API_BASE}/message/reply",
                headers=self.headers,
                json={
                    "replyToken": reply_token,
                    "messages": messages
                }
            )
            return response.status_code == 200

    async def push_message(self, user_id: str, messages: List[Dict[str, Any]]) -> bool:
        """プッシュメッセージを送信"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{LINE_API_BASE}/message/push",
                headers=self.headers,
                json={
                    "to": user_id,
                    "messages": messages
                }
            )
            return response.status_code == 200

    async def multicast_message(self, user_ids: List[str], messages: List[Dict[str, Any]]) -> bool:
        """複数ユーザーにメッセージを一斉送信"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{LINE_API_BASE}/message/multicast",
                headers=self.headers,
                json={
                    "to": user_ids,
                    "messages": messages
                }
            )
            return response.status_code == 200

    async def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """ユーザープロフィールを取得"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{LINE_API_BASE}/profile/{user_id}",
                headers=self.headers
            )
            if response.status_code == 200:
                return response.json()
            return None

    # ============================================
    # ストレスチェック用メッセージテンプレート
    # ============================================

    def create_stress_check_start_message(self) -> List[Dict[str, Any]]:
        """ストレスチェック開始メッセージ"""
        return [
            {
                "type": "flex",
                "altText": "ストレスチェックのお知らせ",
                "contents": {
                    "type": "bubble",
                    "hero": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "📋 ストレスチェック",
                                "weight": "bold",
                                "size": "xl",
                                "align": "center",
                                "color": "#1DB446"
                            }
                        ],
                        "paddingAll": "20px",
                        "backgroundColor": "#F0FFF0"
                    },
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "今月のストレスチェックの時間です",
                                "wrap": True,
                                "size": "md"
                            },
                            {
                                "type": "text",
                                "text": "5つの質問に答えてください（約1分）",
                                "wrap": True,
                                "size": "sm",
                                "color": "#666666",
                                "margin": "md"
                            }
                        ]
                    },
                    "footer": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "button",
                                "style": "primary",
                                "color": "#1DB446",
                                "action": {
                                    "type": "postback",
                                    "label": "開始する",
                                    "data": "action=start_stress_check"
                                }
                            }
                        ]
                    }
                }
            }
        ]

    def create_question_message(self, question_num: int, question_text: str) -> List[Dict[str, Any]]:
        """質問メッセージ（クイック返信付き）"""
        return [
            {
                "type": "text",
                "text": f"Q{question_num}. {question_text}",
                "quickReply": {
                    "items": [
                        {
                            "type": "action",
                            "action": {
                                "type": "postback",
                                "label": "😊 全くない",
                                "data": f"action=answer&q={question_num}&score=1",
                                "displayText": "全くない"
                            }
                        },
                        {
                            "type": "action",
                            "action": {
                                "type": "postback",
                                "label": "🙂 少しある",
                                "data": f"action=answer&q={question_num}&score=2",
                                "displayText": "少しある"
                            }
                        },
                        {
                            "type": "action",
                            "action": {
                                "type": "postback",
                                "label": "😐 ある程度",
                                "data": f"action=answer&q={question_num}&score=3",
                                "displayText": "ある程度"
                            }
                        },
                        {
                            "type": "action",
                            "action": {
                                "type": "postback",
                                "label": "😟 かなりある",
                                "data": f"action=answer&q={question_num}&score=4",
                                "displayText": "かなりある"
                            }
                        }
                    ]
                }
            }
        ]

    def create_completion_message(self, is_high_stress: bool) -> List[Dict[str, Any]]:
        """完了メッセージ"""
        if is_high_stress:
            return [
                {
                    "type": "flex",
                    "altText": "ストレスチェック完了",
                    "contents": {
                        "type": "bubble",
                        "body": {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "✅ 回答ありがとうございます",
                                    "weight": "bold",
                                    "size": "lg"
                                },
                                {
                                    "type": "text",
                                    "text": "結果を確認しました。",
                                    "margin": "md",
                                    "wrap": True
                                },
                                {
                                    "type": "text",
                                    "text": "ストレスが高めの傾向があります。無理せず、必要であれば相談窓口をご利用ください。",
                                    "margin": "md",
                                    "wrap": True,
                                    "color": "#FF6B6B"
                                }
                            ]
                        },
                        "footer": {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "button",
                                    "style": "primary",
                                    "color": "#5865F2",
                                    "action": {
                                        "type": "postback",
                                        "label": "💬 AIに相談する",
                                        "data": "action=start_chat"
                                    }
                                }
                            ]
                        }
                    }
                }
            ]
        else:
            return [
                {
                    "type": "flex",
                    "altText": "ストレスチェック完了",
                    "contents": {
                        "type": "bubble",
                        "body": {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "✅ 回答ありがとうございます",
                                    "weight": "bold",
                                    "size": "lg"
                                },
                                {
                                    "type": "text",
                                    "text": "今月のストレスチェックが完了しました。",
                                    "margin": "md",
                                    "wrap": True
                                },
                                {
                                    "type": "text",
                                    "text": "引き続き健康管理にお気をつけください！",
                                    "margin": "md",
                                    "wrap": True,
                                    "color": "#1DB446"
                                }
                            ]
                        }
                    }
                }
            ]

    def create_reminder_message(self) -> List[Dict[str, Any]]:
        """リマインダーメッセージ"""
        return [
            {
                "type": "text",
                "text": "📢 ストレスチェックがまだ完了していません。\n下のボタンから回答をお願いします。",
                "quickReply": {
                    "items": [
                        {
                            "type": "action",
                            "action": {
                                "type": "postback",
                                "label": "📋 回答する",
                                "data": "action=start_stress_check"
                            }
                        }
                    ]
                }
            }
        ]


# シングルトンインスタンス
line_service = LineService()
