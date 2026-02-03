"""
アラートサービス - ストレスチェックに関するアラート管理
"""
from typing import List
from datetime import date
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.db.models import User, StressCheck
from app.models.dashboard import AlertItem
from app.services.notification_service import get_notification_service, NotificationPayload, NotificationType


class AlertPriority:
    """アラート優先度"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AlertService:
    """アラートサービス"""

    # 閾値設定
    HIGH_STRESS_RATE_THRESHOLD = 0.05  # 5%以上で高優先度アラート
    LOW_COMPLETION_RATE_THRESHOLD = 0.80  # 80%未満で中優先度アラート
    SCORE_DECLINE_THRESHOLD = 0.10  # 10%悪化で中優先度アラート

    def __init__(self, db: AsyncSession):
        self.db = db
        self._read_alerts: set[str] = set()

    async def get_all_alerts(
        self,
        company_id: UUID,
        include_read: bool = False
    ) -> List[AlertItem]:
        """すべてのアラートを取得"""
        alerts = []
        high_stress_alerts = await self._check_high_stress_rate(company_id)
        alerts.extend(high_stress_alerts)
        completion_alerts = await self._check_completion_rate(company_id)
        alerts.extend(completion_alerts)
        department_alerts = await self._check_department_score_decline(company_id)
        alerts.extend(department_alerts)
        if not include_read:
            alerts = [a for a in alerts if a.id not in self._read_alerts]
        priority_order = {AlertPriority.HIGH: 0, AlertPriority.MEDIUM: 1, AlertPriority.LOW: 2}
        alerts.sort(key=lambda x: (priority_order.get(x.alert_level, 3), x.created_at), reverse=False)
        return alerts

    async def _check_high_stress_rate(self, company_id: UUID) -> List[AlertItem]:
        """高ストレス者検出アラートをチェック"""
        alerts = []
        users_result = await self.db.execute(
            select(User).where(User.company_id == company_id)
        )
        users = users_result.scalars().all()
        if not users:
            return alerts
        total_employees = len(users)
        user_ids = [user.id for user in users]
        latest_period_result = await self.db.execute(
            select(func.max(StressCheck.period))
            .where(StressCheck.user_id.in_(user_ids))
        )
        latest_period = latest_period_result.scalar()
        if not latest_period:
            return alerts
        high_stress_result = await self.db.execute(
            select(func.count(StressCheck.id))
            .where(
                and_(
                    StressCheck.user_id.in_(user_ids),
                    StressCheck.period == latest_period,
                    StressCheck.is_high_stress == True
                )
            )
        )
        high_stress_count = high_stress_result.scalar() or 0
        if high_stress_count == 0:
            return alerts
        high_stress_rate = high_stress_count / total_employees
        if high_stress_rate >= self.HIGH_STRESS_RATE_THRESHOLD:
            priority = AlertPriority.HIGH
            rate_percent = round(high_stress_rate * 100, 1)
            alerts.append(AlertItem(
                id=f"hs-{company_id}-{latest_period.isoformat()}",
                department_name="全社",
                alert_level=priority,
                message=f"高ストレス者が{high_stress_count}名（{rate_percent}%）検出されました。早急な対応をご検討ください。",
                created_at=date.today()
            ))
        elif high_stress_count > 0:
            rate_percent = round(high_stress_rate * 100, 1)
            alerts.append(AlertItem(
                id=f"hs-low-{company_id}-{latest_period.isoformat()}",
                department_name="全社",
                alert_level=AlertPriority.LOW,
                message=f"高ストレス者が{high_stress_count}名（{rate_percent}%）検出されました。",
                created_at=date.today()
            ))
        return alerts

    async def _check_completion_rate(self, company_id: UUID) -> List[AlertItem]:
        """受検率低下アラートをチェック"""
        alerts = []
        users_result = await self.db.execute(
            select(User).where(User.company_id == company_id)
        )
        users = users_result.scalars().all()
        if not users:
            return alerts
        total_employees = len(users)
        user_ids = [user.id for user in users]
        today = date.today()
        current_period = date(today.year, today.month, 1)
        completed_result = await self.db.execute(
            select(func.count(func.distinct(StressCheck.user_id)))
            .where(
                and_(
                    StressCheck.user_id.in_(user_ids),
                    StressCheck.period == current_period
                )
            )
        )
        completed_count = completed_result.scalar() or 0
        completion_rate = completed_count / total_employees if total_employees > 0 else 0
        if completion_rate < self.LOW_COMPLETION_RATE_THRESHOLD:
            rate_percent = round(completion_rate * 100, 1)
            remaining = total_employees - completed_count
            if completion_rate < 0.50:
                priority = AlertPriority.HIGH
            else:
                priority = AlertPriority.MEDIUM
            alerts.append(AlertItem(
                id=f"cr-{company_id}-{current_period.isoformat()}",
                department_name="全社",
                alert_level=priority,
                message=f"ストレスチェック受検率が{rate_percent}%です。未受検者{remaining}名への受検勧奨をお願いします。",
                created_at=date.today()
            ))
        return alerts

    async def _check_department_score_decline(self, company_id: UUID) -> List[AlertItem]:
        """部署別ストレススコア悪化アラートをチェック"""
        alerts = []
        users_result = await self.db.execute(
            select(User).where(User.company_id == company_id)
        )
        users = users_result.scalars().all()
        if not users:
            return alerts
        user_ids = [user.id for user in users]
        periods_result = await self.db.execute(
            select(StressCheck.period)
            .where(StressCheck.user_id.in_(user_ids))
            .distinct()
            .order_by(StressCheck.period.desc())
            .limit(2)
        )
        periods = periods_result.scalars().all()
        if len(periods) < 2:
            return alerts
        current_period = periods[0]
        previous_period = periods[1]
        current_avg_result = await self.db.execute(
            select(func.avg(StressCheck.total_score))
            .where(
                and_(
                    StressCheck.user_id.in_(user_ids),
                    StressCheck.period == current_period
                )
            )
        )
        current_avg = current_avg_result.scalar()
        previous_avg_result = await self.db.execute(
            select(func.avg(StressCheck.total_score))
            .where(
                and_(
                    StressCheck.user_id.in_(user_ids),
                    StressCheck.period == previous_period
                )
            )
        )
        previous_avg = previous_avg_result.scalar()
        if current_avg is None or previous_avg is None or previous_avg == 0:
            return alerts
        score_change_rate = (current_avg - previous_avg) / previous_avg
        if score_change_rate >= self.SCORE_DECLINE_THRESHOLD:
            change_percent = round(score_change_rate * 100, 1)
            if score_change_rate >= 0.20:
                priority = AlertPriority.HIGH
            else:
                priority = AlertPriority.MEDIUM
            alerts.append(AlertItem(
                id=f"sd-{company_id}-{current_period.isoformat()}",
                department_name="全社",
                alert_level=priority,
                message=f"ストレススコアが前月比{change_percent}%悪化しています。職場環境の改善を検討してください。",
                created_at=date.today()
            ))
        elif score_change_rate <= -self.SCORE_DECLINE_THRESHOLD:
            change_percent = round(abs(score_change_rate) * 100, 1)
            alerts.append(AlertItem(
                id=f"si-{company_id}-{current_period.isoformat()}",
                department_name="全社",
                alert_level=AlertPriority.LOW,
                message=f"ストレススコアが前月比{change_percent}%改善しました。",
                created_at=date.today()
            ))
        return alerts

    def mark_as_read(self, alert_id: str) -> bool:
        """アラートを既読にする"""
        self._read_alerts.add(alert_id)
        return True

    def mark_as_unread(self, alert_id: str) -> bool:
        """アラートを未読に戻す"""
        self._read_alerts.discard(alert_id)
        return True


# グローバル既読状態（本番ではDB管理推奨）
_alert_read_status: set[str] = set()
_alert_notified_status: set[str] = set()


async def get_alerts_for_company(
    db: AsyncSession,
    company_id: UUID,
    include_read: bool = False
) -> List[AlertItem]:
    """会社のアラートを取得するヘルパー関数"""
    service = AlertService(db)
    service._read_alerts = _alert_read_status
    alerts = await service.get_all_alerts(company_id, include_read)

    notification_service = get_notification_service()
    if notification_service.notification_enabled:
        for alert in alerts:
            if alert.id in _alert_notified_status:
                continue
            urgency_map = {"high": 5, "medium": 3, "low": 2}
            payload = NotificationPayload(
                notification_type=NotificationType.SYSTEM_NOTIFICATION,
                title="ストレスチェックアラート",
                message=alert.message,
                department=alert.department_name,
                urgency_level=urgency_map.get(alert.alert_level, 3)
            )
            await notification_service.send_notification(payload)
            _alert_notified_status.add(alert.id)

    return alerts


def mark_alert_as_read(alert_id: str) -> bool:
    """アラートを既読にするヘルパー関数"""
    _alert_read_status.add(alert_id)
    return True


def mark_alert_as_unread(alert_id: str) -> bool:
    """アラートを未読に戻すヘルパー関数"""
    _alert_read_status.discard(alert_id)
    return True
