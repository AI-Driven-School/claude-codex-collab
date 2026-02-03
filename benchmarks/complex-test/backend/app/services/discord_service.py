"""
Discord Bot API連携サービス

Discord Webhook / Bot APIを使用してメッセージを処理します。
"""
import os
import hmac
import hashlib
from typing import Optional, List, Dict, Any
import httpx
from dotenv import load_dotenv
import logging
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

load_dotenv()

logger = logging.getLogger(__name__)

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
DISCORD_PUBLIC_KEY = os.getenv("DISCORD_PUBLIC_KEY", "")
DISCORD_APPLICATION_ID = os.getenv("DISCORD_APPLICATION_ID", "")
DISCORD_API_BASE = "https://discord.com/api/v10"


class DiscordService:
    """Discord Bot API操作クラス"""

    def __init__(self):
        self.bot_token = DISCORD_BOT_TOKEN
        self.public_key = DISCORD_PUBLIC_KEY
        self.application_id = DISCORD_APPLICATION_ID
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bot {self.bot_token}"
        }

    def verify_signature(self, body: bytes, signature: str, timestamp: str) -> bool:
        """
        Discord Webhookの署名を検証

        Args:
            body: リクエストボディ
            signature: X-Signature-Ed25519 ヘッダー
            timestamp: X-Signature-Timestamp ヘッダー

        Returns:
            署名が有効な場合True
        """
        if not self.public_key:
            logger.warning("DISCORD_PUBLIC_KEY が設定されていません")
            return False

        try:
            verify_key = VerifyKey(bytes.fromhex(self.public_key))
            verify_key.verify(f"{timestamp}{body.decode('utf-8')}".encode(), bytes.fromhex(signature))
            return True
        except BadSignatureError:
            logger.warning("Discord署名検証に失敗しました")
            return False
        except Exception as e:
            logger.error(f"署名検証エラー: {e}")
            return False

    async def send_message(
        self,
        channel_id: str,
        content: str,
        embeds: Optional[List[Dict[str, Any]]] = None,
        components: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        チャンネルにメッセージを送信

        Args:
            channel_id: チャンネルID
            content: メッセージテキスト
            embeds: Embed形式のメッセージ
            components: ボタン等のコンポーネント

        Returns:
            APIレスポンス or None（失敗時）
        """
        if not self.bot_token:
            logger.warning("DISCORD_BOT_TOKEN が設定されていません")
            return None

        payload: Dict[str, Any] = {"content": content}
        if embeds:
            payload["embeds"] = embeds
        if components:
            payload["components"] = components

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{DISCORD_API_BASE}/channels/{channel_id}/messages",
                    headers=self.headers,
                    json=payload
                )
                if response.status_code in (200, 201):
                    return response.json()
                logger.error(f"Discordメッセージ送信エラー: {response.status_code} - {response.text}")
                return None
            except Exception as e:
                logger.error(f"Discord API呼び出しエラー: {e}")
                return None

    async def send_dm(
        self,
        user_id: str,
        content: str,
        embeds: Optional[List[Dict[str, Any]]] = None,
        components: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        ユーザーにDMを送信

        Args:
            user_id: DiscordユーザーID
            content: メッセージテキスト
            embeds: Embed形式のメッセージ
            components: ボタン等のコンポーネント

        Returns:
            APIレスポンス or None（失敗時）
        """
        # DMチャンネルを作成/取得
        dm_channel = await self.create_dm_channel(user_id)
        if not dm_channel:
            return None

        return await self.send_message(dm_channel, content, embeds, components)

    async def create_dm_channel(self, user_id: str) -> Optional[str]:
        """
        ユーザーとのDMチャンネルを作成/取得

        Args:
            user_id: DiscordユーザーID

        Returns:
            DMチャンネルID or None
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{DISCORD_API_BASE}/users/@me/channels",
                    headers=self.headers,
                    json={"recipient_id": user_id}
                )
                if response.status_code in (200, 201):
                    return response.json().get("id")
                logger.error(f"DMチャンネル作成エラー: {response.status_code} - {response.text}")
                return None
            except Exception as e:
                logger.error(f"Discord API呼び出しエラー: {e}")
                return None

    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        ユーザー情報を取得

        Args:
            user_id: DiscordユーザーID

        Returns:
            ユーザー情報 or None
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{DISCORD_API_BASE}/users/{user_id}",
                    headers=self.headers
                )
                if response.status_code == 200:
                    return response.json()
                return None
            except Exception as e:
                logger.error(f"ユーザー情報取得エラー: {e}")
                return None

    async def create_interaction_response(
        self,
        interaction_id: str,
        interaction_token: str,
        response_type: int,
        content: str = None,
        embeds: Optional[List[Dict[str, Any]]] = None,
        components: Optional[List[Dict[str, Any]]] = None,
        flags: int = 0
    ) -> bool:
        """
        インタラクションに応答

        Args:
            interaction_id: インタラクションID
            interaction_token: インタラクショントークン
            response_type: 応答タイプ（4=メッセージ, 6=更新, 7=コンポーネント更新）
            content: メッセージテキスト
            embeds: Embed形式のメッセージ
            components: ボタン等のコンポーネント
            flags: メッセージフラグ（64=エフェメラル）

        Returns:
            成功時True
        """
        payload: Dict[str, Any] = {"type": response_type}

        if response_type == 4 or response_type == 7:
            data: Dict[str, Any] = {}
            if content:
                data["content"] = content
            if embeds:
                data["embeds"] = embeds
            if components:
                data["components"] = components
            if flags:
                data["flags"] = flags
            payload["data"] = data

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{DISCORD_API_BASE}/interactions/{interaction_id}/{interaction_token}/callback",
                    headers={"Content-Type": "application/json"},
                    json=payload
                )
                return response.status_code in (200, 201, 204)
            except Exception as e:
                logger.error(f"インタラクション応答エラー: {e}")
                return False

    async def followup_message(
        self,
        interaction_token: str,
        content: str,
        embeds: Optional[List[Dict[str, Any]]] = None,
        components: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        インタラクションのフォローアップメッセージを送信

        Args:
            interaction_token: インタラクショントークン
            content: メッセージテキスト
            embeds: Embed形式のメッセージ
            components: ボタン等のコンポーネント

        Returns:
            APIレスポンス or None
        """
        payload: Dict[str, Any] = {"content": content}
        if embeds:
            payload["embeds"] = embeds
        if components:
            payload["components"] = components

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{DISCORD_API_BASE}/webhooks/{self.application_id}/{interaction_token}",
                    headers={"Content-Type": "application/json"},
                    json=payload
                )
                if response.status_code in (200, 201):
                    return response.json()
                logger.error(f"フォローアップメッセージエラー: {response.status_code} - {response.text}")
                return None
            except Exception as e:
                logger.error(f"Discord API呼び出しエラー: {e}")
                return None

    # ============================================
    # メッセージテンプレート
    # ============================================

    def create_greeting_embed(self, user_name: str) -> Dict[str, Any]:
        """挨拶メッセージを作成"""
        return {
            "embeds": [
                {
                    "title": f"{user_name}さん、こんにちは！",
                    "description": "私はメンタルヘルスサポートBotです。お気軽にお話しください。",
                    "color": 0x5865F2  # Discord Blurple
                }
            ],
            "components": [
                {
                    "type": 1,  # Action Row
                    "components": [
                        {
                            "type": 2,  # Button
                            "style": 1,  # Primary
                            "label": "ストレスチェック開始",
                            "custom_id": "start_stress_check"
                        },
                        {
                            "type": 2,
                            "style": 2,  # Secondary
                            "label": "AIに相談",
                            "custom_id": "start_chat"
                        }
                    ]
                }
            ]
        }

    def create_casual_check_embed(self) -> Dict[str, Any]:
        """カジュアルな問いかけメッセージを作成"""
        return {
            "embeds": [
                {
                    "title": "調子はどうですか？",
                    "description": "今日の調子を教えてください。何かあればお気軽にお話しください。",
                    "color": 0xFFD700  # Gold
                }
            ],
            "components": [
                {
                    "type": 1,
                    "components": [
                        {
                            "type": 2,
                            "style": 3,  # Success (Green)
                            "label": "元気",
                            "custom_id": "mood_good"
                        },
                        {
                            "type": 2,
                            "style": 2,
                            "label": "普通",
                            "custom_id": "mood_normal"
                        },
                        {
                            "type": 2,
                            "style": 4,  # Danger (Red)
                            "label": "ちょっと疲れた",
                            "custom_id": "mood_tired"
                        }
                    ]
                }
            ]
        }

    def create_stress_check_question_embed(self, question_num: int, question_text: str) -> Dict[str, Any]:
        """ストレスチェック質問メッセージを作成"""
        return {
            "embeds": [
                {
                    "title": f"Q{question_num}. {question_text}",
                    "color": 0x5865F2
                }
            ],
            "components": [
                {
                    "type": 1,
                    "components": [
                        {
                            "type": 2,
                            "style": 2,
                            "label": "全くない",
                            "custom_id": f"stress_answer_{question_num}_1"
                        },
                        {
                            "type": 2,
                            "style": 2,
                            "label": "少しある",
                            "custom_id": f"stress_answer_{question_num}_2"
                        },
                        {
                            "type": 2,
                            "style": 2,
                            "label": "ある程度",
                            "custom_id": f"stress_answer_{question_num}_3"
                        },
                        {
                            "type": 2,
                            "style": 4,
                            "label": "かなりある",
                            "custom_id": f"stress_answer_{question_num}_4"
                        }
                    ]
                }
            ]
        }

    def create_stress_check_result_embed(self, is_high_stress: bool, total_score: int) -> Dict[str, Any]:
        """ストレスチェック結果メッセージを作成"""
        if is_high_stress:
            return {
                "embeds": [
                    {
                        "title": "ストレスチェックが完了しました",
                        "description": f"⚠️ ストレスが高めの傾向があります（スコア: {total_score}）\n\n無理せず、必要であればAIカウンセラーに相談してください。",
                        "color": 0xFF6B6B  # Red
                    }
                ],
                "components": [
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
            }
        else:
            return {
                "embeds": [
                    {
                        "title": "ストレスチェックが完了しました",
                        "description": f"✨ 現在のストレスレベルは正常範囲内です（スコア: {total_score}）\n\n引き続き健康管理にお気をつけください！",
                        "color": 0x57F287  # Green
                    }
                ],
                "components": []
            }

    def create_ai_response_embed(self, reply: str) -> Dict[str, Any]:
        """AI応答メッセージを作成"""
        return {
            "embeds": [
                {
                    "description": reply,
                    "color": 0x5865F2,
                    "footer": {
                        "text": "🤖 AIカウンセラーからの返信"
                    }
                }
            ],
            "components": []
        }

    def create_stress_check_notification_embed(self) -> Dict[str, Any]:
        """ストレスチェック通知メッセージを作成"""
        return {
            "embeds": [
                {
                    "title": "📋 ストレスチェックのお知らせ",
                    "description": "今月のストレスチェックの時間です\n\n5つの質問に答えてください（約1分）",
                    "color": 0x57F287
                }
            ],
            "components": [
                {
                    "type": 1,
                    "components": [
                        {
                            "type": 2,
                            "style": 1,
                            "label": "開始する",
                            "custom_id": "start_stress_check"
                        }
                    ]
                }
            ]
        }

    def create_reminder_embed(self) -> Dict[str, Any]:
        """リマインダーメッセージを作成"""
        return {
            "embeds": [
                {
                    "title": "🔔 ストレスチェックリマインダー",
                    "description": "ストレスチェックがまだ完了していません。\n\n下のボタンから回答をお願いします。",
                    "color": 0xFEE75C  # Yellow
                }
            ],
            "components": [
                {
                    "type": 1,
                    "components": [
                        {
                            "type": 2,
                            "style": 1,
                            "label": "回答する",
                            "custom_id": "start_stress_check"
                        }
                    ]
                }
            ]
        }


# シングルトンインスタンス
discord_service = DiscordService()
