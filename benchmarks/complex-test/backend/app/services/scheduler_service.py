"""
スケジューラーサービス - APSchedulerを使った定期実行管理
"""
import logging
import os
from datetime import datetime
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from dotenv import load_dotenv

from app.db.database import AsyncSessionLocal
from app.services.reminder_service import reminder_service

load_dotenv()

logger = logging.getLogger(__name__)

# 環境変数からリマインダー設定を取得
# デフォルト: 毎週月曜日の9:00と木曜日の9:00に実行
REMINDER_ENABLED = os.getenv("REMINDER_ENABLED", "true").lower() == "true"
REMINDER_CRON_HOUR = int(os.getenv("REMINDER_CRON_HOUR", "9"))
REMINDER_CRON_MINUTE = int(os.getenv("REMINDER_CRON_MINUTE", "0"))
REMINDER_CRON_DAY_OF_WEEK = os.getenv("REMINDER_CRON_DAY_OF_WEEK", "mon,thu")


class SchedulerService:
    """スケジューラーサービス"""

    def __init__(self):
        self.scheduler: Optional[AsyncIOScheduler] = None
        self._initialized = False

    def _job_listener(self, event):
        """ジョブ実行イベントのリスナー"""
        if event.exception:
            logger.error(f"Job {event.job_id} failed: {event.exception}")
        else:
            logger.info(f"Job {event.job_id} executed successfully")

    async def send_stress_check_reminders(self):
        """
        ストレスチェック未受検者へのリマインダー送信ジョブ
        """
        logger.info(f"Executing reminder job at {datetime.now()}")

        try:
            async with AsyncSessionLocal() as db:
                stats = await reminder_service.send_all_reminders(db)
                logger.info(f"Reminder job result: {stats}")
        except Exception as e:
            logger.error(f"Reminder job failed: {e}")
            raise

    def start(self):
        """スケジューラーを開始"""
        if self._initialized:
            logger.warning("Scheduler already initialized")
            return

        if not REMINDER_ENABLED:
            logger.info("Reminder scheduler is disabled")
            return

        self.scheduler = AsyncIOScheduler()
        self.scheduler.add_listener(self._job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

        # リマインダージョブを追加
        trigger = CronTrigger(
            day_of_week=REMINDER_CRON_DAY_OF_WEEK,
            hour=REMINDER_CRON_HOUR,
            minute=REMINDER_CRON_MINUTE,
            timezone="Asia/Tokyo"
        )

        self.scheduler.add_job(
            self.send_stress_check_reminders,
            trigger=trigger,
            id="stress_check_reminder",
            name="ストレスチェック未受検者リマインダー",
            replace_existing=True
        )

        self.scheduler.start()
        self._initialized = True
        logger.info(
            f"Scheduler started. Reminder job scheduled for "
            f"{REMINDER_CRON_DAY_OF_WEEK} at {REMINDER_CRON_HOUR:02d}:{REMINDER_CRON_MINUTE:02d} JST"
        )

    def shutdown(self):
        """スケジューラーを停止"""
        if self.scheduler:
            self.scheduler.shutdown(wait=False)
            self._initialized = False
            logger.info("Scheduler shutdown")

    def get_jobs(self) -> list:
        """登録されているジョブ一覧を取得"""
        if not self.scheduler:
            return []
        return [
            {
                "id": job.id,
                "name": job.name,
                "next_run_time": str(job.next_run_time) if job.next_run_time else None
            }
            for job in self.scheduler.get_jobs()
        ]

    async def trigger_reminder_now(self) -> dict:
        """リマインダーを即時実行（テスト・手動実行用）"""
        logger.info("Triggering reminder job manually")
        async with AsyncSessionLocal() as db:
            return await reminder_service.send_all_reminders(db)


# シングルトンインスタンス
scheduler_service = SchedulerService()
