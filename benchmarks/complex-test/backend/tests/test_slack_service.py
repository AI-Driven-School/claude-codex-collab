"""
Slackサービスのテスト
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import hmac
import hashlib
import time

from app.services.slack_service import SlackService


class TestSlackService:
    """SlackServiceのテスト"""

    @pytest.fixture
    def slack_service(self):
        service = SlackService()
        service.signing_secret = "test_signing_secret"
        service.bot_token = "xoxb-test-token"
        return service

    def test_verify_signature_valid(self, slack_service):
        """有効な署名の検証"""
        body = b'{"test": "data"}'
        timestamp = str(int(time.time()))

        # 正しい署名を生成
        sig_basestring = f"v0:{timestamp}:{body.decode('utf-8')}"
        expected_signature = "v0=" + hmac.new(
            slack_service.signing_secret.encode("utf-8"),
            sig_basestring.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        result = slack_service.verify_signature(body, timestamp, expected_signature)
        assert result is True

    def test_verify_signature_invalid(self, slack_service):
        """無効な署名の検証"""
        body = b'{"test": "data"}'
        timestamp = str(int(time.time()))
        invalid_signature = "v0=invalid_signature"

        result = slack_service.verify_signature(body, timestamp, invalid_signature)
        assert result is False

    def test_verify_signature_old_timestamp(self, slack_service):
        """古いタイムスタンプの検証（5分以上前）"""
        body = b'{"test": "data"}'
        old_timestamp = str(int(time.time()) - 600)  # 10分前
        signature = "v0=any_signature"

        result = slack_service.verify_signature(body, old_timestamp, signature)
        assert result is False

    def test_verify_signature_no_secret(self, slack_service):
        """署名シークレットが設定されていない場合"""
        slack_service.signing_secret = ""
        body = b'{"test": "data"}'
        timestamp = str(int(time.time()))
        signature = "v0=any_signature"

        result = slack_service.verify_signature(body, timestamp, signature)
        assert result is False

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.post")
    async def test_post_message_success(self, mock_post, slack_service):
        """メッセージ送信成功"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"ok": True, "ts": "1234567890.123456"}
        mock_post.return_value = mock_response

        with patch("httpx.AsyncClient.__aenter__", return_value=MagicMock(post=mock_post)):
            with patch("httpx.AsyncClient.__aexit__", return_value=None):
                result = await slack_service.post_message(
                    channel="C1234567890",
                    text="Test message"
                )

        assert result is not None

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.post")
    async def test_post_message_no_token(self, mock_post, slack_service):
        """トークンなしでメッセージ送信"""
        slack_service.bot_token = ""

        result = await slack_service.post_message(
            channel="C1234567890",
            text="Test message"
        )

        assert result is None

    def test_create_greeting_message(self, slack_service):
        """挨拶メッセージ生成"""
        result = slack_service.create_greeting_message("テストユーザー")

        assert "text" in result
        assert "blocks" in result
        assert "テストユーザー" in result["text"]

    def test_create_casual_check_message(self, slack_service):
        """カジュアルチェックメッセージ生成"""
        result = slack_service.create_casual_check_message()

        assert "text" in result
        assert "blocks" in result
        assert "調子" in result["text"]

        # アクションボタンがあることを確認
        actions_block = next(
            (b for b in result["blocks"] if b["type"] == "actions"),
            None
        )
        assert actions_block is not None
        assert len(actions_block["elements"]) == 3  # 元気, 普通, ちょっと疲れた

    def test_create_stress_check_question(self, slack_service):
        """ストレスチェック質問メッセージ生成"""
        result = slack_service.create_stress_check_question(1, "テスト質問？")

        assert "text" in result
        assert "blocks" in result
        assert "Q1" in result["text"]

        # 4つの選択肢があることを確認
        actions_block = next(
            (b for b in result["blocks"] if b["type"] == "actions"),
            None
        )
        assert actions_block is not None
        assert len(actions_block["elements"]) == 4

    def test_create_stress_check_result_high_stress(self, slack_service):
        """高ストレス結果メッセージ生成"""
        result = slack_service.create_stress_check_result(is_high_stress=True, total_score=18)

        assert "text" in result
        assert "blocks" in result
        assert "高ストレス" in result["text"] or "warning" in str(result["blocks"])

    def test_create_stress_check_result_normal(self, slack_service):
        """正常ストレス結果メッセージ生成"""
        result = slack_service.create_stress_check_result(is_high_stress=False, total_score=8)

        assert "text" in result
        assert "blocks" in result
        assert "正常" in str(result["blocks"]) or "sparkles" in str(result["blocks"])

    def test_create_ai_response_message(self, slack_service):
        """AI応答メッセージ生成"""
        reply = "お話しいただきありがとうございます。"
        result = slack_service.create_ai_response_message(reply)

        assert "text" in result
        assert "blocks" in result
        assert reply in result["text"]
