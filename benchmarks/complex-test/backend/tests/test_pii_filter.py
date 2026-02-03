"""
PIIフィルターのテスト
"""
import os
import pytest

os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"

from app.utils.pii_filter import clean_pii


class TestCleanPii:
    """PII除去のテスト"""

    def test_email_replacement(self):
        """メールアドレスの除去"""
        text = "連絡先は test@example.com です"
        result = clean_pii(text)
        assert "[EMAIL]" in result
        assert "test@example.com" not in result

    def test_multiple_emails(self):
        """複数のメールアドレス"""
        text = "送信元: sender@test.co.jp, 送信先: receiver@company.com"
        result = clean_pii(text)
        assert result.count("[EMAIL]") == 2

    def test_phone_with_hyphens(self):
        """ハイフン付き電話番号"""
        text = "電話番号は 03-1234-5678 です"
        result = clean_pii(text)
        assert "[PHONE]" in result
        assert "03-1234-5678" not in result

    def test_phone_mobile_with_hyphens(self):
        """携帯電話（ハイフン付き）"""
        text = "携帯は 090-1234-5678 です"
        result = clean_pii(text)
        assert "[PHONE]" in result
        assert "090-1234-5678" not in result

    def test_phone_without_hyphens(self):
        """ハイフンなし電話番号"""
        text = "電話番号は 0312345678 です"
        result = clean_pii(text)
        assert "[PHONE]" in result
        assert "0312345678" not in result

    def test_employee_id(self):
        """社員番号の除去"""
        text = "私の社員番号は EMP-12345 です"
        result = clean_pii(text)
        assert "[EMPLOYEE_ID]" in result
        assert "EMP-12345" not in result

    def test_mixed_pii(self):
        """複合パターン"""
        text = "担当者: EMP-99999, メール: admin@example.com, 電話: 03-0000-0000"
        result = clean_pii(text)
        assert "[EMPLOYEE_ID]" in result
        assert "[EMAIL]" in result
        assert "[PHONE]" in result

    def test_no_pii(self):
        """PIIがないテキスト"""
        text = "今日は天気が良いですね"
        result = clean_pii(text)
        assert result == text

    def test_empty_text(self):
        """空のテキスト"""
        result = clean_pii("")
        assert result == ""

    def test_partial_email_not_replaced(self):
        """メールアドレスの一部は置換しない"""
        text = "ユーザー名@"
        result = clean_pii(text)
        assert "ユーザー名@" in result

    def test_preserves_surrounding_text(self):
        """周囲のテキストは保持"""
        text = "お問い合わせは contact@example.com までお願いします。"
        result = clean_pii(text)
        assert "お問い合わせは" in result
        assert "までお願いします。" in result
        assert "[EMAIL]" in result
