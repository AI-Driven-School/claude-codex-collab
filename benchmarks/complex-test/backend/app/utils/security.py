"""
セキュリティ関連ユーティリティ（JWT、パスワードハッシュ）
"""
import re
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
import os
from dotenv import load_dotenv

load_dotenv()

# JWT設定 - 本番環境では必ず環境変数を設定すること
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError(
        "JWT_SECRET_KEY environment variable is required. "
        "Generate a secure key with: openssl rand -hex 32"
    )

ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "30"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# パスワード複雑性要件
PASSWORD_MIN_LENGTH = 8
PASSWORD_REQUIRE_UPPERCASE = True
PASSWORD_REQUIRE_LOWERCASE = True
PASSWORD_REQUIRE_DIGIT = True
PASSWORD_REQUIRE_SPECIAL = True


def validate_password_complexity(password: str) -> tuple[bool, str]:
    """
    パスワードの複雑性を検証

    Returns:
        tuple[bool, str]: (有効かどうか, エラーメッセージ)
    """
    if len(password) < PASSWORD_MIN_LENGTH:
        return False, f"パスワードは{PASSWORD_MIN_LENGTH}文字以上で入力してください"

    if PASSWORD_REQUIRE_UPPERCASE and not re.search(r"[A-Z]", password):
        return False, "パスワードには大文字を1文字以上含めてください"

    if PASSWORD_REQUIRE_LOWERCASE and not re.search(r"[a-z]", password):
        return False, "パスワードには小文字を1文字以上含めてください"

    if PASSWORD_REQUIRE_DIGIT and not re.search(r"\d", password):
        return False, "パスワードには数字を1文字以上含めてください"

    if PASSWORD_REQUIRE_SPECIAL and not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "パスワードには特殊文字（!@#$%^&*など）を1文字以上含めてください"

    return True, ""


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """パスワード検証"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """パスワードハッシュ化"""
    return pwd_context.hash(password)


def _create_token(data: dict, token_type: str, expires_delta: Optional[timedelta] = None) -> str:
    """JWTトークン作成"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        if token_type == "refresh":
            expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": token_type})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """JWTアクセストークン作成"""
    return _create_token(data, "access", expires_delta)


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """JWTリフレッシュトークン作成"""
    return _create_token(data, "refresh", expires_delta)


def _decode_token(token: str, expected_type: str) -> Optional[dict]:
    """JWTトークン復号化"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != expected_type:
            return None
        return payload
    except JWTError:
        return None


def decode_access_token(token: str) -> Optional[dict]:
    """JWTアクセストークン復号化"""
    return _decode_token(token, "access")


def decode_refresh_token(token: str) -> Optional[dict]:
    """JWTリフレッシュトークン復号化"""
    return _decode_token(token, "refresh")
