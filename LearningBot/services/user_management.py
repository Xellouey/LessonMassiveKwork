"""
Сервис для управления пользователями

⚠️ ЗАКОММЕНТИРОВАН - НЕ ИСПОЛЬЗУЕТСЯ В УПРОЩЕННОЙ ВЕРСИИ БОТА
Данный сервис содержит избыточный функционал для простого образовательного бота:
- Поиск пользователей
- Блокировка/разблокировка
- Удаление пользователей
- Детальная статистика пользователей

Для простого бота достаточно базового UserService
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, desc, and_, or_
from sqlalchemy.orm import selectinload
from database.models import User, Purchase, Lesson
# from database.models import UserActivity  # ❌ Закомментировано для MVP

logger = logging.getLogger(__name__)


class UserManagementService:
    """Сервис для управления пользователями в административной панели"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_all_users(self, limit: int = 50, offset: int = 0) -> List[User]:
        """Получить всех пользователей с пагинацией"""
        try:
            result = await self.session.execute(
                select(User)
                .order_by(desc(User.registration_date))
                .limit(limit)
                .offset(offset)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Ошибка при получении списка пользователей: {e}")
            return []
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Получить пользователя по Telegram user_id"""
        try:
            result = await self.session.execute(
                select(User).where(User.user_id == user_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Ошибка при получении пользователя {user_id}: {e}")
            return None
    
    async def search_users(self, query: str) -> List[User]:
        """Поиск пользователей по username, имени или user_id"""
        try:
            # Проверяем, является ли запрос числом (user_id)
            if query.isdigit():
                user_id = int(query)
                result = await self.session.execute(
                    select(User).where(User.user_id == user_id)
                )
                user = result.scalar_one_or_none()
                return [user] if user else []
            
            # Поиск по username и full_name (регистронезависимый)
            search_pattern = f"%{query}%"
            search_pattern_lower = f"%{query.lower()}%"
            
            result = await self.session.execute(
                select(User).where(
                    or_(
                        User.username.ilike(search_pattern),
                        User.full_name.ilike(search_pattern),
                        User.full_name.like(search_pattern),  # Для кириллицы
                        User.username.like(search_pattern_lower)
                    )
                ).order_by(desc(User.registration_date))
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Ошибка при поиске пользователей по запросу '{query}': {e}")
            return []
    
    async def block_user(self, user_id: int) -> bool:
        """Заблокировать пользователя"""
        try:
            result = await self.session.execute(
                update(User)
                .where(User.user_id == user_id)
                .values(is_active=False)
            )
            await self.session.commit()
            
            return result.rowcount > 0
        except Exception as e:
            logger.error(f"Ошибка при блокировке пользователя {user_id}: {e}")
            await self.session.rollback()
            return False
    
    async def unblock_user(self, user_id: int) -> bool:
        """Разблокировать пользователя"""
        try:
            result = await self.session.execute(
                update(User)
                .where(User.user_id == user_id)
                .values(is_active=True)
            )
            await self.session.commit()
            
            return result.rowcount > 0
        except Exception as e:
            logger.error(f"Ошибка при разблокировке пользователя {user_id}: {e}")
            await self.session.rollback()
            return False
    
    async def delete_user(self, user_id: int) -> bool:
        """Удалить пользователя (осторожно!)"""
        try:
            # Сначала удаляем связанные записи
            await self.session.execute(
                # delete(UserActivity).where(UserActivity.user_id == user_id)  # ❌ Закомментировано для MVP
            )
            await self.session.execute(
                delete(Purchase).where(Purchase.user_id == user_id)
            )
            
            # Затем удаляем самого пользователя
            result = await self.session.execute(
                delete(User).where(User.user_id == user_id)
            )
            await self.session.commit()
            
            return result.rowcount > 0
        except Exception as e:
            logger.error(f"Ошибка при удалении пользователя {user_id}: {e}")
            await self.session.rollback()
            return False
    
    async def get_user_statistics(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получить детальную статистику пользователя"""
        try:
            # Получаем основную информацию о пользователе
            user_result = await self.session.execute(
                select(User).where(User.user_id == user_id)
            )
            user = user_result.scalar_one_or_none()
            
            if not user:
                return None
            
            # Получаем количество покупок
            purchases_count_result = await self.session.execute(
                select(func.count(Purchase.id)).where(
                    and_(
                        Purchase.user_id == user.user_id,  # Используем Telegram user_id
                        Purchase.status == "completed"
                    )
                )
            )
            total_purchases = purchases_count_result.scalar() or 0
            
            # Получаем общую сумму трат
            total_spent_result = await self.session.execute(
                select(func.sum(Purchase.amount_stars)).where(
                    and_(
                        Purchase.user_id == user.user_id,  # Используем Telegram user_id
                        Purchase.status == "completed"
                    )
                )
            )
            total_spent = total_spent_result.scalar() or 0
            
            # Получаем количество активностей
            activities_count_result = await self.session.execute(
                # select(func.count(UserActivity.id)).where(
                #     UserActivity.user_id == user.user_id  # Используем Telegram user_id
                # )  # ❌ Закомментировано для MVP
                select(func.count(1))  # Простая заглушка для MVP
            )
            total_activities = activities_count_result.scalar() or 0
            
            # Получаем последнюю покупку
            last_purchase_result = await self.session.execute(
                select(Purchase.purchase_date).where(
                    and_(
                        Purchase.user_id == user.user_id,  # Используем Telegram user_id
                        Purchase.status == "completed"
                    )
                ).order_by(desc(Purchase.purchase_date)).limit(1)
            )
            last_purchase = last_purchase_result.scalar_one_or_none()
            
            return {
                'user_id': user.user_id,
                'full_name': user.full_name,
                'username': user.username,
                'language': user.language,
                'registration_date': user.registration_date,
                'last_activity': user.last_activity,
                'is_active': user.is_active,
                'total_purchases': total_purchases,
                'total_spent': total_spent,
                'total_activities': total_activities,
                'last_purchase': last_purchase
            }
        except Exception as e:
            logger.error(f"Ошибка при получении статистики пользователя {user_id}: {e}")
            return None
    
    async def get_user_purchases(self, user_id: int, limit: int = 10) -> List[Purchase]:
        """Получить покупки пользователя"""
        try:
            result = await self.session.execute(
                select(Purchase)
                .options(selectinload(Purchase.lesson))
                .where(Purchase.user_id == user_id)
                .order_by(desc(Purchase.purchase_date))
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Ошибка при получении покупок пользователя {user_id}: {e}")
            return []
    
    async def get_active_users(self, limit: int = 50) -> List[User]:
        """Получить активных (незаблокированных) пользователей"""
        try:
            result = await self.session.execute(
                select(User)
                .where(User.is_active == True)
                .order_by(desc(User.last_activity))
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Ошибка при получении активных пользователей: {e}")
            return []
    
    async def get_blocked_users(self, limit: int = 50) -> List[User]:
        """Получить заблокированных пользователей"""
        try:
            result = await self.session.execute(
                select(User)
                .where(User.is_active == False)
                .order_by(desc(User.registration_date))
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Ошибка при получении заблокированных пользователей: {e}")
            return []
    
    async def get_recent_users(self, days: int = 7, limit: int = 50) -> List[User]:
        """Получить недавно зарегистрированных пользователей"""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            result = await self.session.execute(
                select(User)
                .where(User.registration_date >= cutoff_date)
                .order_by(desc(User.registration_date))
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Ошибка при получении недавних пользователей: {e}")
            return []
    
    async def get_top_buyers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Получить топ покупателей по общей сумме трат"""
        try:
            result = await self.session.execute(
                select(
                    User.user_id,
                    User.full_name,
                    User.username,
                    func.count(Purchase.id).label('purchases_count'),
                    func.sum(Purchase.amount_stars).label('total_spent')
                )
                .join(Purchase, User.user_id == Purchase.user_id)
                .where(Purchase.status == "completed")
                .group_by(User.user_id, User.full_name, User.username)
                .order_by(desc('total_spent'))
                .limit(limit)
            )
            
            top_buyers = []
            for row in result.all():
                top_buyers.append({
                    'user_id': row.user_id,
                    'full_name': row.full_name,
                    'username': row.username,
                    'purchases_count': row.purchases_count,
                    'total_spent': row.total_spent
                })
            
            return top_buyers
        except Exception as e:
            logger.error(f"Ошибка при получении топ покупателей: {e}")
            return []
    
    async def get_users_count(self) -> Dict[str, int]:
        """Получить общее количество пользователей по категориям"""
        try:
            # Общее количество
            total_result = await self.session.execute(
                select(func.count(User.id))
            )
            total_users = total_result.scalar() or 0
            
            # Активные пользователи
            active_result = await self.session.execute(
                select(func.count(User.id)).where(User.is_active == True)
            )
            active_users = active_result.scalar() or 0
            
            # Заблокированные пользователи
            blocked_users = total_users - active_users
            
            # Недавно зарегистрированные (за последние 7 дней)
            week_ago = datetime.now(timezone.utc) - timedelta(days=7)
            recent_result = await self.session.execute(
                select(func.count(User.id)).where(
                    User.registration_date >= week_ago
                )
            )
            recent_users = recent_result.scalar() or 0
            
            return {
                'total': total_users,
                'active': active_users,
                'blocked': blocked_users,
                'recent': recent_users
            }
        except Exception as e:
            logger.error(f"Ошибка при получении количества пользователей: {e}")
            return {
                'total': 0,
                'active': 0,
                'blocked': 0,
                'recent': 0
            }