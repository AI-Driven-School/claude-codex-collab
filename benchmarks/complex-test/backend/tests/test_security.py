"""
セキュリティユーティリティのテスト
"""
import os
import pytest

# テスト用環境変数を設定
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"


class TestPasswordValidation:
    """パスワード検証のテスト"""

    def test_valid_password(self):
        """有効なパスワード"""
        from app.utils.security import validate_password_complexity

        is_valid, error = validate_password_complexity("TestPassword123!")
        assert is_valid is True
        assert error == ""

    def test_password_too_short(self):
        """短すぎるパスワード"""
        from app.utils.security import validate_password_complexity

        is_valid, error = validate_password_complexity("Test1!")
        assert is_valid is False
        assert "8文字以上" in error

    def test_password_no_uppercase(self):
        """大文字なしパスワード"""
        from app.utils.security import validate_password_complexity

        is_valid, error = validate_password_complexity("testpassword123!")
        assert is_valid is False
        assert "大文字" in error

    def test_password_no_lowercase(self):
        """小文字なしパスワード"""
        from app.utils.security import validate_password_complexity

        is_valid, error = validate_password_complexity("TESTPASSWORD123!")
        assert is_valid is False
        assert "小文字" in error

    def test_password_no_digit(self):
        """数字なしパスワード"""
        from app.utils.security import validate_password_complexity

        is_valid, error = validate_password_complexity("TestPassword!")
        assert is_valid is False
        assert "数字" in error

    def test_password_no_special(self):
        """特殊文字なしパスワード"""
        from app.utils.security import validate_password_complexity

        is_valid, error = validate_password_complexity("TestPassword123")
        assert is_valid is False
        assert "特殊文字" in error


class TestPasswordHashing:
    """パスワードハッシュのテスト"""

    def test_hash_and_verify(self):
        """ハッシュ化と検証"""
        from app.utils.security import get_password_hash, verify_password

        password = "TestPassword123!"
        hashed = get_password_hash(password)

        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("wrong_password", hashed) is False

    def test_hash_is_different_each_time(self):
        """同じパスワードでもハッシュは毎回異なる"""
        from app.utils.security import get_password_hash

        password = "TestPassword123!"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        assert hash1 != hash2


class TestJWT:
    """JWTトークンのテスト"""

    def test_create_and_decode_access_token(self):
        """アクセストークンの作成と復号"""
        from app.utils.security import create_access_token, decode_access_token

        data = {"sub": "user-123", "role": "admin"}
        token = create_access_token(data)
        decoded = decode_access_token(token)

        assert decoded is not None
        assert decoded["sub"] == "user-123"
        assert decoded["role"] == "admin"
        assert decoded["type"] == "access"

    def test_create_and_decode_refresh_token(self):
        """リフレッシュトークンの作成と復号"""
        from app.utils.security import create_refresh_token, decode_refresh_token

        data = {"sub": "user-123", "role": "admin"}
        token = create_refresh_token(data)
        decoded = decode_refresh_token(token)

        assert decoded is not None
        assert decoded["sub"] == "user-123"
        assert decoded["type"] == "refresh"

    def test_access_token_cannot_be_decoded_as_refresh(self):
        """アクセストークンはリフレッシュトークンとして復号できない"""
        from app.utils.security import create_access_token, decode_refresh_token

        token = create_access_token({"sub": "user-123"})
        decoded = decode_refresh_token(token)

        assert decoded is None

    def test_refresh_token_cannot_be_decoded_as_access(self):
        """リフレッシュトークンはアクセストークンとして復号できない"""
        from app.utils.security import create_refresh_token, decode_access_token

        token = create_refresh_token({"sub": "user-123"})
        decoded = decode_access_token(token)

        assert decoded is None

    def test_invalid_token_returns_none(self):
        """無効なトークンはNoneを返す"""
        from app.utils.security import decode_access_token

        decoded = decode_access_token("invalid-token")
        assert decoded is None
