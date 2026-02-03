"""
Microsoft Teams Incoming Webhook通知サービス

Teams Incoming Webhookを使用して通知を送信します。
"""
import os
from typing import Optional, Dict, Any, List
import httpx
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

TEAMS_WEBHOOK_URL = os.getenv("TEAMS_WEBHOOK_URL", "")


class TeamsService:
    """Microsoft Teams Webhook通知サービス"""

    def __init__(self):
        self.webhook_url = TEAMS_WEBHOOK_URL

    def is_configured(self) -> bool:
        """Teams Webhookが設定されているか確認"""
        return bool(self.webhook_url)

    async def send_message(
        self,
        title: str,
        message: str,
        color: str = "0076D7",
        facts: Optional[List[Dict[str, str]]] = None
    ) -> bool:
        """
        Teams Incoming Webhookにメッセージを送信

        Args:
            title: メッセージタイトル
            message: メッセージ本文
            color: テーマカラー（16進数）
            facts: 追加のファクト情報（key-valueペア）

        Returns:
            成功時True
        """
        if not self.is_configured():
            logger.warning("TEAMS_WEBHOOK_URL が設定されていません")
            return False

        # Adaptive Card形式のペイロード
        payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": color,
            "summary": title,
            "sections": [
                {
                    "activityTitle": title,
                    "text": message,
                    "markdown": True
                }
            ]
        }

        # ファクト情報を追加
        if facts:
            payload["sections"][0]["facts"] = facts

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.webhook_url,
                    json=payload,
                    timeout=10.0
                )
                if response.status_code == 200:
                    logger.info("Teamsメッセージ送信成功")
                    return True
                else:
                    logger.error(f"Teamsメッセージ送信エラー: {response.status_code} - {response.text}")
                    return False
            except Exception as e:
                logger.error(f"Teams API呼び出しエラー: {e}")
                return False

    async def send_stress_check_reminder(
        self,
        pending_count: int,
        period: str,
        deadline: Optional[str] = None
    ) -> bool:
        """
        ストレスチェックリマインド通知を送信

        Args:
            pending_count: 未受検者数
            period: 実施期間（例: 2024年1月）
            deadline: 締め切り日（オプション）

        Returns:
            成功時True
        """
        title = "ストレスチェックリマインド"

        facts = [
            {"name": "対象期間", "value": period},
            {"name": "未受検者数", "value": f"{pending_count}名"}
        ]

        if deadline:
            facts.append({"name": "締め切り", "value": deadline})

        message = f"**{pending_count}名**の従業員がストレスチェックを未受検です。\n\n期限内に受検を完了するよう、対象者への声かけをお願いします。"

        return await self.send_message(
            title=title,
            message=message,
            color="FFA500",  # オレンジ
            facts=facts
        )

    async def send_high_stress_alert(
        self,
        department: Optional[str] = None,
        alert_count: int = 1,
        urgency_level: int = 1
    ) -> bool:
        """
        高ストレスアラート通知を送信

        Args:
            department: 部署名（オプション）
            alert_count: アラート対象者数
            urgency_level: 緊急度レベル（1-3）

        Returns:
            成功時True
        """
        title = "高ストレスアラート"

        # 緊急度に応じた色設定
        color_map = {
            1: "FF8C00",  # ダークオレンジ
            2: "FF4500",  # レッドオレンジ
            3: "FF0000"   # 赤
        }
        color = color_map.get(urgency_level, "FF8C00")

        facts = [
            {"name": "対象者数", "value": f"{alert_count}名"},
            {"name": "緊急度", "value": f"レベル{urgency_level}"}
        ]

        if department:
            facts.insert(0, {"name": "部署", "value": department})

        message = "高ストレスが検出されました。\n\n産業医面談の検討や、対象者へのフォローアップをお願いします。"

        return await self.send_message(
            title=title,
            message=message,
            color=color,
            facts=facts
        )

    async def send_completion_notification(
        self,
        period: str,
        total_count: int,
        completed_count: int,
        completion_rate: float
    ) -> bool:
        """
        ストレスチェック完了通知を送信

        Args:
            period: 実施期間
            total_count: 対象者総数
            completed_count: 受検完了者数
            completion_rate: 受検率（0.0-1.0）

        Returns:
            成功時True
        """
        title = "ストレスチェック完了報告"

        facts = [
            {"name": "対象期間", "value": period},
            {"name": "対象者数", "value": f"{total_count}名"},
            {"name": "受検完了者", "value": f"{completed_count}名"},
            {"name": "受検率", "value": f"{completion_rate * 100:.1f}%"}
        ]

        # 受検率に応じた色設定
        if completion_rate >= 0.9:
            color = "28A745"  # 緑
            status = "目標達成"
        elif completion_rate >= 0.7:
            color = "FFA500"  # オレンジ
            status = "概ね順調"
        else:
            color = "DC3545"  # 赤
            status = "要フォロー"

        message = f"**{period}**のストレスチェックが完了しました。\n\n受検率: **{completion_rate * 100:.1f}%**（{status}）"

        return await self.send_message(
            title=title,
            message=message,
            color=color,
            facts=facts
        )

    async def send_test_message(self) -> bool:
        """
        テストメッセージを送信

        Returns:
            成功時True
        """
        return await self.send_message(
            title="StressAgent Pro - テスト通知",
            message="Teams連携が正常に動作しています。\n\nこれはテストメッセージです。",
            color="0076D7",
            facts=[
                {"name": "ステータス", "value": "接続成功"},
                {"name": "サービス", "value": "StressAgent Pro"}
            ]
        )


# シングルトンインスタンス
teams_service = TeamsService()
