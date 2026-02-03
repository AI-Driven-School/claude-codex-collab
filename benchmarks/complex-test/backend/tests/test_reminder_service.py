"""
リマインダーサービスのテスト
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import date
import uuid

from app.services.reminder_service import ReminderService


class TestReminderService:
    """ReminderServiceのテスト"""

    @pytest.fixture
    def reminder_service(self):
        return ReminderService()

    @pytest.fixture
    def mock_user(self):
        """モックユーザーを作成"""
        user = MagicMock()
        user.id = uuid.uuid4()
        user.email = "test@example.com"
        user.line_user_id = "U1234567890abcdef"
        user.company_id = uuid.uuid4()
        return user

    @pytest.fixture
    def mock_db(self):
        """モックDBセッションを作成"""
        db = AsyncMock()
        return db

    @pytest.mark.asyncio
    async def test_send_reminder_to_users_empty_list(self, reminder_service):
        """空のユーザーリストの場合"""
        result = await reminder_service.send_reminder_to_users([])
        assert result["sent"] == 0
        assert result["failed"] == 0
        assert result["total"] == 0

    @pytest.mark.asyncio
    async def test_send_reminder_to_users_no_line_users(self, reminder_service, mock_user):
        """LINE連携なしユーザーの場合"""
        mock_user.line_user_id = None
        result = await reminder_service.send_reminder_to_users([mock_user])
        assert result["sent"] == 0
        assert result["total"] == 0

    @pytest.mark.asyncio
    @patch("app.services.reminder_service.line_service")
    async def test_send_reminder_to_users_success(
        self, mock_line_service, reminder_service, mock_user
    ):
        """正常にリマインダーを送信"""
        mock_line_service.multicast_message = AsyncMock(return_value=True)
        mock_line_service.create_reminder_message.return_value = [{"type": "text", "text": "test"}]

        result = await reminder_service.send_reminder_to_users([mock_user])

        assert result["sent"] == 1
        assert result["failed"] == 0
        assert result["total"] == 1
        mock_line_service.multicast_message.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.services.reminder_service.line_service")
    async def test_send_reminder_to_users_failure(
        self, mock_line_service, reminder_service, mock_user
    ):
        """リマインダー送信失敗"""
        mock_line_service.multicast_message = AsyncMock(return_value=False)
        mock_line_service.create_reminder_message.return_value = [{"type": "text", "text": "test"}]

        result = await reminder_service.send_reminder_to_users([mock_user])

        assert result["sent"] == 0
        assert result["failed"] == 1
        assert result["total"] == 1

    @pytest.mark.asyncio
    @patch("app.services.reminder_service.line_service")
    async def test_send_reminder_batch_processing(
        self, mock_line_service, reminder_service
    ):
        """500人超えの場合のバッチ処理"""
        # 600人のモックユーザーを作成
        users = []
        for i in range(600):
            user = MagicMock()
            user.id = uuid.uuid4()
            user.line_user_id = f"U{i:016d}"
            users.append(user)

        mock_line_service.multicast_message = AsyncMock(return_value=True)
        mock_line_service.create_reminder_message.return_value = [{"type": "text", "text": "test"}]

        result = await reminder_service.send_reminder_to_users(users)

        # 2回に分けて送信されることを確認（500 + 100）
        assert mock_line_service.multicast_message.call_count == 2
        assert result["sent"] == 600
        assert result["total"] == 600
