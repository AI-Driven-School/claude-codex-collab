"""
Slack/Teams通知サービス

外部メッセージングプラットフォームへの通知送信機能を提供します。
"""
import os
import httpx
import logging
from typing import Optional, Dict, Any, List
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class NotificationType(str, Enum):
    """通知タイプ"""
    HIGH_STRESS_ALERT = "high_stress_alert"
    WEEKLY_REPORT = "weekly_report"
    URGENT_INTERVENTION = "urgent_intervention"
    SYSTEM_NOTIFICATION = "system_notification"


@dataclass
class NotificationPayload:
    """通知ペイロード"""
    notification_type: NotificationType
    title: str
    message: str
    user_name: Optional[str] = None
    department: Optional[str] = None
    urgency_level: int = 1  # 1-5
    additional_data: Optional[Dict[str, Any]] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class NotificationService:
    """Slack/Teamsへの通知送信サービス"""

    def __init__(self):
        self.slack_webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        self.teams_webhook_url = os.getenv("TEAMS_WEBHOOK_URL")
        self.notification_enabled = os.getenv("NOTIFICATION_ENABLED", "false").lower() == "true"
        self.high_stress_threshold = float(os.getenv("HIGH_STRESS_THRESHOLD", "-0.5"))
        self._client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """HTTPクライアントをクローズ"""
        await self._client.aclose()

    def _build_slack_payload(self, payload: NotificationPayload) -> Dict[str, Any]:
        """Slack Block Kit形式のペイロードを構築"""
        color_map = {
            1: "#36a64f",  # 緑: 低
            2: "#2196F3",  # 青: やや低
            3: "#FFC107",  # 黄: 中
            4: "#FF9800",  # オレンジ: やや高
            5: "#F44336"   # 赤: 高
        }
        color = color_map.get(payload.urgency_level, "#808080")

        emoji_map = {
            NotificationType.HIGH_STRESS_ALERT: ":warning:",
            NotificationType.WEEKLY_REPORT: ":bar_chart:",
            NotificationType.URGENT_INTERVENTION: ":rotating_light:",
            NotificationType.SYSTEM_NOTIFICATION: ":bell:"
        }
        emoji = emoji_map.get(payload.notification_type, ":bell:")

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} {payload.title}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": payload.message
                }
            }
        ]

        # 追加情報があれば表示
        fields = []
        if payload.department:
            fields.append({
                "type": "mrkdwn",
                "text": f"*部署:*\n{payload.department}"
            })
        if payload.urgency_level:
            urgency_text = ["低", "やや低", "中", "やや高", "高"][payload.urgency_level - 1]
            fields.append({
                "type": "mrkdwn",
                "text": f"*緊急度:*\n{urgency_text}"
            })

        if fields:
            blocks.append({
                "type": "section",
                "fields": fields
            })

        # タイムスタンプ
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"送信時刻: {payload.timestamp.strftime('%Y-%m-%d %H:%M:%S')} UTC"
                }
            ]
        })

        return {
            "blocks": blocks,
            "attachments": [{
                "color": color,
                "fallback": f"{payload.title}: {payload.message}"
            }]
        }

    def _build_teams_payload(self, payload: NotificationPayload) -> Dict[str, Any]:
        """Teams Adaptive Card形式のペイロードを構築"""
        color_map = {
            1: "Good",
            2: "Default",
            3: "Warning",
            4: "Warning",
            5: "Attention"
        }
        theme_color = {
            1: "00FF00",
            2: "0078D4",
            3: "FFC107",
            4: "FF9800",
            5: "FF0000"
        }

        facts = []
        if payload.department:
            facts.append({
                "title": "部署",
                "value": payload.department
            })
        if payload.urgency_level:
            urgency_text = ["低", "やや低", "中", "やや高", "高"][payload.urgency_level - 1]
            facts.append({
                "title": "緊急度",
                "value": urgency_text
            })
        facts.append({
            "title": "送信時刻",
            "value": payload.timestamp.strftime('%Y-%m-%d %H:%M:%S') + " UTC"
        })

        return {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": theme_color.get(payload.urgency_level, "0078D4"),
            "summary": payload.title,
            "sections": [{
                "activityTitle": payload.title,
                "activitySubtitle": payload.notification_type.value,
                "facts": facts,
                "text": payload.message,
                "markdown": True
            }]
        }

    async def send_to_slack(self, payload: NotificationPayload) -> bool:
        """Slackに通知を送信"""
        if not self.slack_webhook_url:
            logger.warning("Slack Webhook URLが設定されていません")
            return False

        try:
            slack_payload = self._build_slack_payload(payload)
            response = await self._client.post(
                self.slack_webhook_url,
                json=slack_payload
            )
            if response.status_code == 200:
                logger.info(f"Slack通知を送信しました: {payload.title}")
                return True
            else:
                logger.error(f"Slack通知に失敗しました: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Slack通知でエラーが発生しました: {e}")
            return False

    async def send_to_teams(self, payload: NotificationPayload) -> bool:
        """Teamsに通知を送信"""
        if not self.teams_webhook_url:
            logger.warning("Teams Webhook URLが設定されていません")
            return False

        try:
            teams_payload = self._build_teams_payload(payload)
            response = await self._client.post(
                self.teams_webhook_url,
                json=teams_payload
            )
            if response.status_code == 200:
                logger.info(f"Teams通知を送信しました: {payload.title}")
                return True
            else:
                logger.error(f"Teams通知に失敗しました: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Teams通知でエラーが発生しました: {e}")
            return False

    async def send_notification(self, payload: NotificationPayload) -> Dict[str, bool]:
        """すべての設定されたプラットフォームに通知を送信"""
        results = {}

        if self.slack_webhook_url:
            results["slack"] = await self.send_to_slack(payload)

        if self.teams_webhook_url:
            results["teams"] = await self.send_to_teams(payload)

        return results

    async def notify_high_stress_detected(
        self,
        user_name: Optional[str] = None,
        department: Optional[str] = None,
        stress_score: Optional[float] = None,
        risk_factors: Optional[List[str]] = None
    ) -> Dict[str, bool]:
        """高ストレス検出時の通知"""
        message_parts = ["高ストレスの兆候が検出されました。"]

        if stress_score is not None:
            message_parts.append(f"感情スコア: {stress_score:.2f}")

        if risk_factors:
            message_parts.append(f"リスク要因: {', '.join(risk_factors)}")

        message_parts.append("早期対応を検討してください。")

        payload = NotificationPayload(
            notification_type=NotificationType.HIGH_STRESS_ALERT,
            title="高ストレスアラート",
            message="\n".join(message_parts),
            user_name=user_name,
            department=department,
            urgency_level=4
        )

        return await self.send_notification(payload)


# シングルトンインスタンス
_notification_service: Optional[NotificationService] = None


def get_notification_service() -> NotificationService:
    """通知サービスのシングルトンインスタンスを取得"""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service


async def check_and_notify_high_stress(
    sentiment_score: float,
    urgency: int = 1,
    risk_flags: Optional[List[str]] = None,
    topics: Optional[List[str]] = None
) -> Dict[str, bool]:
    """高ストレス検出時の通知を確認・送信するヘルパー関数"""
    service = get_notification_service()

    if not service.notification_enabled:
        return {"enabled": False}

    if sentiment_score < service.high_stress_threshold:
        risk_factors = []
        if risk_flags:
            risk_factors.extend(risk_flags)
        if topics:
            risk_factors.extend(topics)

        return await service.notify_high_stress_detected(
            stress_score=sentiment_score,
            risk_factors=risk_factors if risk_factors else None
        )

    return {"triggered": False}
