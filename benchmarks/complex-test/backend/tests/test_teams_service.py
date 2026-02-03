"""
Teamsサービスのテスト
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.teams_service import TeamsService


class TestTeamsService:
    """TeamsServiceのテスト"""

    @pytest.fixture
    def teams_service(self):
        service = TeamsService()
        service.webhook_url = "https://example.com/teams-webhook"
        return service

    def test_is_configured_true(self, teams_service):
        """Webhook設定済み判定"""
        assert teams_service.is_configured() is True

    def test_is_configured_false(self):
        """Webhook未設定判定"""
        service = TeamsService()
        service.webhook_url = ""
        assert service.is_configured() is False

    @pytest.mark.asyncio
    async def test_send_message_success(self, teams_service):
        """メッセージ送信成功"""
        mock_response = MagicMock(status_code=200, text="ok")
        mock_post = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient.__aenter__", return_value=MagicMock(post=mock_post)):
            with patch("httpx.AsyncClient.__aexit__", return_value=None):
                result = await teams_service.send_message(
                    title="テストタイトル",
                    message="テスト本文",
                    color="123456",
                    facts=[{"name": "key", "value": "value"}]
                )

        assert result is True
        args, kwargs = mock_post.call_args
        assert args[0] == teams_service.webhook_url
        assert kwargs["timeout"] == 10.0
        payload = kwargs["json"]
        assert payload["summary"] == "テストタイトル"
        assert payload["themeColor"] == "123456"
        assert payload["sections"][0]["text"] == "テスト本文"
        assert payload["sections"][0]["facts"] == [{"name": "key", "value": "value"}]

    @pytest.mark.asyncio
    async def test_send_message_not_configured(self):
        """Webhook未設定時の送信"""
        service = TeamsService()
        service.webhook_url = ""
        result = await service.send_message(
            title="テスト",
            message="本文"
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_send_message_http_error(self, teams_service):
        """メッセージ送信失敗（HTTPエラー）"""
        mock_response = MagicMock(status_code=500, text="error")
        mock_post = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient.__aenter__", return_value=MagicMock(post=mock_post)):
            with patch("httpx.AsyncClient.__aexit__", return_value=None):
                result = await teams_service.send_message(
                    title="テストタイトル",
                    message="テスト本文"
                )

        assert result is False

    @pytest.mark.asyncio
    async def test_send_message_exception(self, teams_service):
        """メッセージ送信失敗（例外）"""
        mock_post = AsyncMock(side_effect=RuntimeError("boom"))

        with patch("httpx.AsyncClient.__aenter__", return_value=MagicMock(post=mock_post)):
            with patch("httpx.AsyncClient.__aexit__", return_value=None):
                result = await teams_service.send_message(
                    title="テストタイトル",
                    message="テスト本文"
                )

        assert result is False

    @pytest.mark.asyncio
    async def test_send_stress_check_reminder_success(self, teams_service):
        """ストレスチェックリマインド送信成功"""
        with patch.object(TeamsService, "send_message", new=AsyncMock(return_value=True)) as mock_send:
            result = await teams_service.send_stress_check_reminder(
                pending_count=3,
                period="2024年1月",
                deadline="2024/01/31"
            )

        assert result is True
        _, kwargs = mock_send.call_args
        assert kwargs["title"] == "ストレスチェックリマインド"
        assert kwargs["color"] == "FFA500"
        assert any(f["name"] == "締め切り" for f in kwargs["facts"])

    @pytest.mark.asyncio
    async def test_send_stress_check_reminder_failure(self, teams_service):
        """ストレスチェックリマインド送信失敗"""
        with patch.object(TeamsService, "send_message", new=AsyncMock(return_value=False)):
            result = await teams_service.send_stress_check_reminder(
                pending_count=1,
                period="2024年2月"
            )

        assert result is False

    @pytest.mark.asyncio
    async def test_send_high_stress_alert_success(self, teams_service):
        """高ストレスアラート送信成功"""
        with patch.object(TeamsService, "send_message", new=AsyncMock(return_value=True)) as mock_send:
            result = await teams_service.send_high_stress_alert(
                department="開発部",
                alert_count=5,
                urgency_level=3
            )

        assert result is True
        _, kwargs = mock_send.call_args
        assert kwargs["title"] == "高ストレスアラート"
        assert kwargs["color"] == "FF0000"
        assert kwargs["facts"][0]["name"] == "部署"
        assert kwargs["facts"][0]["value"] == "開発部"

    @pytest.mark.asyncio
    async def test_send_high_stress_alert_failure(self, teams_service):
        """高ストレスアラート送信失敗"""
        with patch.object(TeamsService, "send_message", new=AsyncMock(return_value=False)):
            result = await teams_service.send_high_stress_alert(
                alert_count=2,
                urgency_level=2
            )

        assert result is False

    @pytest.mark.asyncio
    async def test_send_completion_notification_success(self, teams_service):
        """完了通知送信成功"""
        with patch.object(TeamsService, "send_message", new=AsyncMock(return_value=True)) as mock_send:
            result = await teams_service.send_completion_notification(
                period="2024年1月",
                total_count=100,
                completed_count=95,
                completion_rate=0.95
            )

        assert result is True
        _, kwargs = mock_send.call_args
        assert kwargs["title"] == "ストレスチェック完了報告"
        assert kwargs["color"] == "28A745"
        assert "目標達成" in kwargs["message"]

    @pytest.mark.asyncio
    async def test_send_completion_notification_failure(self, teams_service):
        """完了通知送信失敗"""
        with patch.object(TeamsService, "send_message", new=AsyncMock(return_value=False)):
            result = await teams_service.send_completion_notification(
                period="2024年1月",
                total_count=100,
                completed_count=50,
                completion_rate=0.5
            )

        assert result is False

    @pytest.mark.asyncio
    async def test_send_test_message_success(self, teams_service):
        """テストメッセージ送信成功"""
        with patch.object(TeamsService, "send_message", new=AsyncMock(return_value=True)) as mock_send:
            result = await teams_service.send_test_message()

        assert result is True
        _, kwargs = mock_send.call_args
        assert kwargs["title"] == "StressAgent Pro - テスト通知"
        assert kwargs["color"] == "0076D7"

    @pytest.mark.asyncio
    async def test_send_test_message_failure(self, teams_service):
        """テストメッセージ送信失敗"""
        with patch.object(TeamsService, "send_message", new=AsyncMock(return_value=False)):
            result = await teams_service.send_test_message()

        assert result is False
