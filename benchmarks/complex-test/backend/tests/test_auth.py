"""
認証エンドポイントのテスト
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestRegister:
    """ユーザー登録のテスト"""

    async def test_register_success(self, client: AsyncClient, test_user_data: dict):
        """正常な登録"""
        response = await client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == 200

        data = response.json()
        assert "user" in data
        assert data["user"]["email"] == test_user_data["email"]
        assert data["user"]["role"] == "admin"

    async def test_register_password_mismatch(self, client: AsyncClient, test_user_data: dict):
        """パスワード不一致"""
        test_user_data["password_confirm"] = "DifferentPassword123!"
        response = await client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == 400
        assert "一致しません" in response.json()["detail"]

    async def test_register_weak_password(self, client: AsyncClient, test_user_data: dict):
        """弱いパスワード"""
        test_user_data["password"] = "weak"
        test_user_data["password_confirm"] = "weak"
        response = await client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == 400

    async def test_register_duplicate_email(self, client: AsyncClient, test_user_data: dict):
        """重複メールアドレス"""
        # 最初の登録
        await client.post("/api/v1/auth/register", json=test_user_data)

        # 同じメールで再登録
        response = await client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == 400
        assert "既に登録" in response.json()["detail"]


@pytest.mark.asyncio
class TestLogin:
    """ログインのテスト"""

    async def test_login_success(self, client: AsyncClient, test_user_data: dict, test_login_data: dict):
        """正常なログイン"""
        # ユーザー登録
        await client.post("/api/v1/auth/register", json=test_user_data)

        # ログイン
        response = await client.post("/api/v1/auth/login", json=test_login_data)
        assert response.status_code == 200

        data = response.json()
        assert "user" in data
        assert data["user"]["email"] == test_login_data["email"]

    async def test_login_wrong_password(self, client: AsyncClient, test_user_data: dict):
        """間違ったパスワード"""
        # ユーザー登録
        await client.post("/api/v1/auth/register", json=test_user_data)

        # 間違ったパスワードでログイン
        response = await client.post("/api/v1/auth/login", json={
            "email": test_user_data["email"],
            "password": "WrongPassword123!"
        })
        assert response.status_code == 401

    async def test_login_nonexistent_user(self, client: AsyncClient):
        """存在しないユーザー"""
        response = await client.post("/api/v1/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "TestPassword123!"
        })
        assert response.status_code == 401


@pytest.mark.asyncio
class TestLogout:
    """ログアウトのテスト"""

    async def test_logout(self, client: AsyncClient):
        """ログアウト"""
        response = await client.post("/api/v1/auth/logout")
        assert response.status_code == 200
        assert response.json()["message"] == "logged_out"


@pytest.mark.asyncio
class TestGetMe:
    """現在のユーザー取得のテスト"""

    async def test_get_me_unauthorized(self, client: AsyncClient):
        """未認証"""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401

    async def test_get_me_with_cookie(self, client: AsyncClient, test_user_data: dict):
        """Cookie認証でユーザー情報取得"""
        # 登録
        register_response = await client.post("/api/v1/auth/register", json=test_user_data)
        assert register_response.status_code == 200

        # Cookieが設定されているはず
        cookies = register_response.cookies

        # /me を呼び出し
        response = await client.get("/api/v1/auth/me", cookies=cookies)
        assert response.status_code == 200
        assert response.json()["email"] == test_user_data["email"]
