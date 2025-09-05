"""
Сервис для работы со статистикой

ℹ️ УПРОЩЕНО ДЛЯ MVP - Убрана сложная аналитика по UserActivity
Оставлена только базовая статистика для админки
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from database.models import User, Lesson, Purchase
# from database.models import UserActivity  # ❌ Закомментировано для MVP

logger = logging.getLogger(__name__)


class StatisticsService:
    """Сервис для получения статистики системы"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_general_stats(self) -> Dict[str, Any]:
        """Получить общую статистику системы"""
        try:
            # Общее количество пользователей
            total_users_result = await self.session.execute(
                select(func.count(User.id))
            )
            total_users = total_users_result.scalar() or 0
            
            # Активные пользователи (заходили в последние 30 дней)
            thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
            active_users_result = await self.session.execute(
                select(func.count(User.id)).where(
                    User.last_activity >= thirty_days_ago
                )
            )
            active_users = active_users_result.scalar() or 0
            
            # Общее количество уроков
            total_lessons_result = await self.session.execute(
                select(func.count(Lesson.id))
            )
            total_lessons = total_lessons_result.scalar() or 0
            
            # Активные уроки
            active_lessons_result = await self.session.execute(
                select(func.count(Lesson.id)).where(Lesson.is_active == True)
            )
            active_lessons = active_lessons_result.scalar() or 0
            
            # Общее количество покупок
            total_purchases_result = await self.session.execute(
                select(func.count(Purchase.id)).where(
                    Purchase.status == "completed"
                )
            )
            total_purchases = total_purchases_result.scalar() or 0
            
            # Общий доход
            total_revenue_result = await self.session.execute(
                select(func.sum(Purchase.amount_stars)).where(
                    Purchase.status == "completed"
                )
            )
            total_revenue = total_revenue_result.scalar() or 0
            
            return {
                'total_users': total_users,
                'active_users': active_users,
                'total_lessons': total_lessons,
                'active_lessons': active_lessons,
                'total_purchases': total_purchases,
                'total_revenue': total_revenue,
                'revenue_per_user': round(total_revenue / total_users, 2) if total_users > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Ошибка при получении общей статистики: {e}")
            return {}
    
    async def get_revenue_stats(self, days: int = 30) -> Dict[str, Any]:
        """Получить статистику доходов за период"""
        try:
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days)
            
            # Доход за период
            period_revenue_result = await self.session.execute(
                select(func.sum(Purchase.amount_stars)).where(
                    and_(
                        Purchase.status == "completed",
                        Purchase.purchase_date >= start_date,
                        Purchase.purchase_date <= end_date
                    )
                )
            )
            period_revenue = period_revenue_result.scalar() or 0
            
            # Количество покупок за период
            period_purchases_result = await self.session.execute(
                select(func.count(Purchase.id)).where(
                    and_(
                        Purchase.status == "completed",
                        Purchase.purchase_date >= start_date,
                        Purchase.purchase_date <= end_date
                    )
                )
            )
            period_purchases = period_purchases_result.scalar() or 0
            
            # Средний чек
            avg_purchase = round(period_revenue / period_purchases, 2) if period_purchases > 0 else 0
            
            # Доход по дням (последние 7 дней)
            daily_revenue = []
            for i in range(7):
                day_start = end_date - timedelta(days=i+1)
                day_end = end_date - timedelta(days=i)
                
                day_revenue_result = await self.session.execute(
                    select(func.sum(Purchase.amount_stars)).where(
                        and_(
                            Purchase.status == "completed",
                            Purchase.purchase_date >= day_start,
                            Purchase.purchase_date < day_end
                        )
                    )
                )
                day_revenue = day_revenue_result.scalar() or 0
                daily_revenue.append({
                    'date': day_start.strftime('%d.%m'),
                    'revenue': day_revenue
                })
            
            return {
                'period_days': days,
                'period_revenue': period_revenue,
                'period_purchases': period_purchases,
                'avg_purchase': avg_purchase,
                'daily_revenue': list(reversed(daily_revenue))
            }
            
        except Exception as e:
            logger.error(f"Ошибка при получении статистики доходов: {e}")
            return {}
    
    async def get_top_lessons(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Получить топ уроков по продажам"""
        try:
            result = await self.session.execute(
                select(
                    Lesson.title,
                    Lesson.price_stars,
                    func.count(Purchase.id).label('sales_count'),
                    func.sum(Purchase.amount_stars).label('total_revenue')
                )
                .join(Purchase, Lesson.id == Purchase.lesson_id)
                .where(Purchase.status == "completed")
                .group_by(Lesson.id, Lesson.title, Lesson.price_stars)
                .order_by(desc('sales_count'))
                .limit(limit)
            )
            
            top_lessons = []
            for row in result.all():
                top_lessons.append({
                    'title': row.title,
                    'price': row.price_stars,
                    'sales': row.sales_count,
                    'revenue': row.total_revenue
                })
            
            return top_lessons
            
        except Exception as e:
            logger.error(f"Ошибка при получении топ уроков: {e}")
            return []
    
    # ❌ ЗАКОММЕНТИРОВАНО ДЛЯ MVP - сложная аналитика по активности не нужна для простого бота
    # async def get_user_activity_stats(self, days: int = 7) -> List[Dict[str, Any]]:
    #     """Получить статистику активности пользователей"""
    #     # Остальная часть метода использует UserActivity которая закомментирована
    #     return []
    
    async def get_conversion_stats(self) -> Dict[str, Any]:
        """Получить статистику конверсии"""
        try:
            # Общее количество пользователей
            total_users_result = await self.session.execute(
                select(func.count(User.id))
            )
            total_users = total_users_result.scalar() or 0
            
            # Количество покупателей (уникальных пользователей с покупками)
            buyers_result = await self.session.execute(
                select(func.count(func.distinct(Purchase.user_id))).where(
                    Purchase.status == "completed"
                )
            )
            buyers = buyers_result.scalar() or 0
            
            # Конверсия в покупку
            conversion_rate = round((buyers / total_users) * 100, 2) if total_users > 0 else 0
            
            # Среднее количество покупок на покупателя
            avg_purchases_result = await self.session.execute(
                select(func.count(Purchase.id) / func.count(func.distinct(Purchase.user_id))).where(
                    Purchase.status == "completed"
                )
            )
            avg_purchases_per_buyer = round(avg_purchases_result.scalar() or 0, 2)
            
            return {
                'total_users': total_users,
                'buyers': buyers,
                'conversion_rate': conversion_rate,
                'avg_purchases_per_buyer': avg_purchases_per_buyer
            }
            
        except Exception as e:
            logger.error(f"Ошибка при получении статистики конверсии: {e}")
            return {}