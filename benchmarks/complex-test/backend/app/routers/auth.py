"""
認証関連エンドポイント
"""
from fastapi import APIRouter, Depends, HTTPException, status, Header, Response, Cookie, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.db.database import get_db
from app.db.models import User, Company, UserRole, PlanType
from app.models.auth import UserRegister, UserLogin, AuthResponse, AuthUser
from app.models.user import UserResponse
from app.utils.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    validate_password_complexity,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS
)
from uuid import UUID
import os

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

# レート制限設定
limiter = Limiter(key_func=get_remote_address)

ACCESS_TOKEN_COOKIE = os.getenv("ACCESS_TOKEN_COOKIE", "access_token")
REFRESH_TOKEN_COOKIE = os.getenv("REFRESH_TOKEN_COOKIE", "refresh_token")
COOKIE_DOMAIN = os.getenv("COOKIE_DOMAIN") or None
COOKIE_SAMESITE = os.getenv("COOKIE_SAMESITE", "lax")
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE,
        value=access_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
        domain=COOKIE_DOMAIN
    )
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE,
        value=refresh_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/",
        domain=COOKIE_DOMAIN
    )


@router.post("/register", response_model=AuthResponse)
@limiter.limit("5/minute")
async def register(
    request: Request,
    user_data: UserRegister,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """企業・ユーザー登録"""
    # パスワード確認
    if user_data.password != user_data.password_confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="パスワードが一致しません"
        )

    # パスワード複雑性チェック
    is_valid, error_message = validate_password_complexity(user_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )

    # メールアドレス重複チェック
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="このメールアドレスは既に登録されています"
        )

    # 企業作成
    company = Company(
        name=user_data.company_name,
        industry=user_data.industry,
        plan_type=PlanType(user_data.plan_type)
    )
    db.add(company)
    await db.flush()

    # ユーザー作成
    user = User(
        company_id=company.id,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        role=UserRole.ADMIN
    )
    db.add(user)
    await db.commit()

    # トークン発行
    token_payload = {"sub": str(user.id), "role": user.role.value}
    access_token = create_access_token(data=token_payload)
    refresh_token = create_refresh_token(data=token_payload)
    _set_auth_cookies(response, access_token, refresh_token)

    return AuthResponse(
        user=AuthUser(
            id=str(user.id),
            email=user.email,
            role=user.role.value,
            company_id=str(user.company_id)
        )
    )


@router.post("/login", response_model=AuthResponse)
@limiter.limit("10/minute")
async def login(
    request: Request,
    credentials: UserLogin,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """ログイン"""
    # ユーザー検索
    result = await db.execute(select(User).where(User.email == credentials.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="メールアドレスまたはパスワードが正しくありません"
        )

    # トークン発行
    token_payload = {"sub": str(user.id), "role": user.role.value}
    access_token = create_access_token(data=token_payload)
    refresh_token = create_refresh_token(data=token_payload)
    _set_auth_cookies(response, access_token, refresh_token)

    return AuthResponse(
        user=AuthUser(
            id=str(user.id),
            email=user.email,
            role=user.role.value,
            company_id=str(user.company_id)
        )
    )


@router.post("/refresh", response_model=AuthResponse)
@limiter.limit("30/minute")
async def refresh_token(
    request: Request,
    response: Response,
    refresh_token: Optional[str] = Cookie(default=None, alias=REFRESH_TOKEN_COOKIE),
    db: AsyncSession = Depends(get_db)
):
    """リフレッシュトークンでアクセストークンを更新"""
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="リフレッシュトークンがありません"
        )

    payload = decode_refresh_token(refresh_token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無効なリフレッシュトークンです"
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="トークンが無効です"
        )

    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ユーザーが見つかりません"
        )

    token_payload = {"sub": str(user.id), "role": user.role.value}
    new_access_token = create_access_token(data=token_payload)
    new_refresh_token = create_refresh_token(data=token_payload)
    _set_auth_cookies(response, new_access_token, new_refresh_token)

    return AuthResponse(
        user=AuthUser(
            id=str(user.id),
            email=user.email,
            role=user.role.value,
            company_id=str(user.company_id)
        )
    )


@router.post("/logout")
async def logout(response: Response):
    """ログアウト（クッキー削除）"""
    response.delete_cookie(ACCESS_TOKEN_COOKIE, path="/", domain=COOKIE_DOMAIN)
    response.delete_cookie(REFRESH_TOKEN_COOKIE, path="/", domain=COOKIE_DOMAIN)
    return {"message": "logged_out"}


async def get_current_user(
    authorization: Optional[str] = Header(None),
    access_token: Optional[str] = Cookie(default=None, alias=ACCESS_TOKEN_COOKIE),
    db: AsyncSession = Depends(get_db)
) -> User:
    """現在のユーザーを取得（依存性注入用）"""
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
    elif access_token:
        token = access_token

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="認証が必要です"
        )
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無効なトークンです"
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="トークンが無効です"
        )

    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ユーザーが見つかりません"
        )

    return user


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """現在のユーザー情報を取得"""
    company_result = await db.execute(
        select(Company).where(Company.id == current_user.company_id)
    )
    company = company_result.scalar_one_or_none()
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        role=current_user.role.value,
        company_id=str(current_user.company_id),
        company_name=company.name if company else None
    )
