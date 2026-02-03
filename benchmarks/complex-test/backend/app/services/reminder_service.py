"""
ストレスチェック未受検者へのリマインドサービス
"""
import logging
from datetime import date
from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User, StressCheck, Company
from app.services.line_service import line_service

logger = logging.getLogger(__name__)


class ReminderService:
    """ストレスチェックリマインドサービス"""

    async def get_non_taken_users_with_line(
        self,
        db: AsyncSession,
        company_id: Optional[str] = None
    ) -> List[User]:
        """
        今月のストレスチェック未受検者（LINE連携済み）を取得

        Args:
            db: データベースセッション
            company_id: 特定企業のみ対象にする場合はそのID

        Returns:
            LINE連携済みの未受検ユーザーリスト
        """
        current_period = date.today().replace(day=1)

        # LINE連携済みユーザーを取得
        query = select(User).where(User.line_user_id.isnot(None))
        if company_id:
            query = query.where(User.company_id == company_id)

        result = await db.execute(query)
        users = result.scalars().all()

        if not users:
            return []

        # 今月受検済みのユーザーIDを取得
        taken_result = await db.execute(
            select(StressCheck.user_id).where(
                and_(
                    StressCheck.period == current_period,
                    StressCheck.user_id.in_([u.id for u in users])
                )
            )
        )
        taken_user_ids = set(row[0] for row in taken_result.fetchall())

        # 未受検者を抽出
        non_taken_users = [u for u in users if u.id not in taken_user_ids]
        return non_taken_users

    async def send_reminder_to_users(
        self,
        users: List[User]
    ) -> dict:
        """
        ユーザーリストにリマインダーを送信

        Args:
            users: 送信対象ユーザーリスト

        Returns:
            送信結果の統計情報
        """
        if not users:
            return {"sent": 0, "failed": 0, "total": 0}

        user_ids = [u.line_user_id for u in users if u.line_user_id]

        if not user_ids:
            return {"sent": 0, "failed": 0, "total": 0}

        messages = line_service.create_reminder_message()

        # LINEのマルチキャストは最大500人まで
        # 500人を超える場合は分割して送信
        batch_size = 500
        sent_count = 0
        failed_count = 0

        for i in range(0, len(user_ids), batch_size):
            batch = user_ids[i:i + batch_size]
            try:
                success = await line_service.multicast_message(batch, messages)
                if success:
                    sent_count += len(batch)
                    logger.info(f"Reminder sent to {len(batch)} users")
                else:
                    failed_count += len(batch)
                    logger.error(f"Failed to send reminder to {len(batch)} users")
            except Exception as e:
                failed_count += len(batch)
                logger.error(f"Error sending reminder: {e}")

        return {
            "sent": sent_count,
            "failed": failed_count,
            "total": len(user_ids)
        }

    async def send_all_reminders(self, db: AsyncSession) -> dict:
        """
        全企業の未受検者にリマインダーを送信

        Args:
            db: データベースセッション

        Returns:
            送信結果の統計情報
        """
        logger.info("Starting automatic reminder job for all companies")

        # 全企業を取得
        result = await db.execute(select(Company))
        companies = result.scalars().all()

        total_stats = {"sent": 0, "failed": 0, "total": 0}

        for company in companies:
            users = await self.get_non_taken_users_with_line(db, str(company.id))
            if users:
                logger.info(f"Sending reminders to {len(users)} users in company {company.name}")
                stats = await self.send_reminder_to_users(users)
                total_stats["sent"] += stats["sent"]
                total_stats["failed"] += stats["failed"]
                total_stats["total"] += stats["total"]

        logger.info(f"Reminder job completed: {total_stats}")
        return total_stats


# シングルトンインスタンス
reminder_service = ReminderService()
