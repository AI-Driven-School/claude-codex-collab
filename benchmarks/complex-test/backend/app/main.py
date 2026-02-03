"""
FastAPIアプリケーションエントリーポイント
"""
from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.routers import auth, stress_check, chat, dashboard, admin, department, reports, csv_import, line_webhook, slack_webhook, teams_webhook, discord_webhook, user, reminder, org_analysis
from app.services.scheduler_service import scheduler_service
import os

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# レート制限設定
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションのライフサイクル管理"""
    # MongoDB接続はスキップ（必要時に設定）
    logger.info("Application started (MongoDB disabled)")

    # スケジューラーを開始
    scheduler_service.start()
    logger.info("Scheduler service started")

    yield

    # スケジューラーを停止
    scheduler_service.shutdown()
    logger.info("Application shutdown")


app = FastAPI(
    title="StressAgent Pro API",
    description="AI駆動型メンタルヘルスSaaS API",
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "auth", "description": "認証関連エンドポイント"},
        {"name": "stress_check", "description": "ストレスチェック関連"},
        {"name": "chat", "description": "AIチャット機能"},
        {"name": "dashboard", "description": "管理者ダッシュボード"},
        {"name": "admin", "description": "管理者機能"},
        {"name": "department", "description": "部署管理"},
        {"name": "reports", "description": "レポート生成"},
        {"name": "user", "description": "ユーザー管理"},
    ]
)

# レート制限ハンドラ登録
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS設定
cors_origins_env = os.getenv("CORS_ALLOW_ORIGINS", "")
cors_origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()]
if not cors_origins:
    cors_origins = ["http://localhost:3000"]

# 本番環境では許可するメソッドとヘッダーを限定
CORS_ALLOW_METHODS = os.getenv("CORS_ALLOW_METHODS", "GET,POST,PUT,DELETE,PATCH,OPTIONS").split(",")
CORS_ALLOW_HEADERS = os.getenv(
    "CORS_ALLOW_HEADERS",
    "Authorization,Content-Type,Accept,Origin,X-Requested-With"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=CORS_ALLOW_METHODS,
    allow_headers=CORS_ALLOW_HEADERS,
)

# ルーター登録
app.include_router(auth.router)
app.include_router(stress_check.router)
app.include_router(chat.router)
app.include_router(dashboard.router)
app.include_router(admin.router)
app.include_router(department.router)
app.include_router(reports.router)
app.include_router(csv_import.router)
app.include_router(line_webhook.router)
app.include_router(slack_webhook.router)
app.include_router(teams_webhook.router)
app.include_router(discord_webhook.router)
app.include_router(user.router)
app.include_router(reminder.router)
app.include_router(org_analysis.router)


@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {"message": "StressAgent Pro API"}


@app.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {"status": "ok"}
