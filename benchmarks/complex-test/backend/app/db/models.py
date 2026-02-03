"""
SQLAlchemyデータベースモデル
"""
from sqlalchemy import Column, String, Boolean, Integer, Float, Date, DateTime, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.db.database import Base


class PlanType(str, enum.Enum):
    """プラン種別"""
    BASIC = "basic"
    PREMIUM = "premium"


class UserRole(str, enum.Enum):
    """ユーザーロール"""
    ADMIN = "admin"
    EMPLOYEE = "employee"
    DOCTOR = "doctor"


class Company(Base):
    """企業テーブル"""
    __tablename__ = "companies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    industry = Column(String, nullable=True)
    plan_type = Column(SQLEnum(PlanType, values_callable=lambda x: [e.value for e in x], create_constraint=False, native_enum=False), nullable=False, default=PlanType.BASIC)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    users = relationship("User", back_populates="company")
    departments = relationship("Department", back_populates="company")


class Department(Base):
    """部署テーブル"""
    __tablename__ = "departments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    company = relationship("Company", back_populates="departments")
    users = relationship("User", back_populates="department")


class User(Base):
    """ユーザーテーブル"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole, values_callable=lambda x: [e.value for e in x], create_constraint=False, native_enum=False), nullable=False, default=UserRole.EMPLOYEE)
    slack_id = Column(String, nullable=True)
    line_user_id = Column(String, nullable=True, index=True)  # LINE連携用
    link_code = Column(String, nullable=True, unique=True)  # 連携コード
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    company = relationship("Company", back_populates="users")
    department = relationship("Department", back_populates="users")
    stress_checks = relationship("StressCheck", back_populates="user")
    daily_scores = relationship("DailyScore", back_populates="user")
    draft_answer = relationship("DraftAnswer", back_populates="user", uselist=False)
    chat_messages = relationship("ChatMessage", back_populates="user")


class StressCheck(Base):
    """ストレスチェックテーブル"""
    __tablename__ = "stress_checks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    period = Column(Date, nullable=False)  # 実施年月（YYYY-MM-01形式で保存）
    answers = Column(JSONB, nullable=False)  # { "q1": 4, "q2": 2, ... }
    total_score = Column(Integer, nullable=False)
    is_high_stress = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="stress_checks")


class DailyScore(Base):
    """日次スコアテーブル（AI推論結果）"""
    __tablename__ = "daily_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False)
    sentiment_score = Column(Float, nullable=False)  # -1.0 to 1.0
    fatigue_level = Column(Integer, nullable=True)  # 1-5
    sleep_hours = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="daily_scores")


class DraftAnswer(Base):
    """ストレスチェック途中保存テーブル"""
    __tablename__ = "draft_answers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    answers = Column(JSONB, nullable=False, default=dict)  # { "q1": 4, "q2": 2, ... }
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="draft_answer")


class ChatMessage(Base):
    """チャットメッセージテーブル"""
    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    role = Column(String, nullable=False)  # "user" or "ai"
    content = Column(String, nullable=False)
    sentiment_score = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="chat_messages")
