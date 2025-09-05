"""
Сервис для работы с пользователями
"""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from database.models import User
# from database.models import UserActivity  # ❌ Закомментировано для MVP
import logging

logger = logging.getLogger(__name__)


class UserService:
    """Сервис для управления пользователями"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_user_by_telegram_id(self, user_id: int) -> Optional[User]:
        """Получить пользователя по Telegram ID"""
        try:
            result = await self.session.execute(
                select(User).where(User.user_id == user_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Ошибка при получении пользователя {user_id}: {e}")
            return None
    
    async def create_user(
        self, 
        user_id: int, 
        username: Optional[str] = None, 
        full_name: str = "Пользователь"
    ) -> Optional[User]:
        """Создать нового пользователя"""
        try:
            user = User(
                user_id=user_id,
                username=username,
                full_name=full_name,
                registration_date=datetime.now(timezone.utc),
                is_active=True,
                language='ru',
                total_spent=0,
                last_activity=datetime.now(timezone.utc)
            )
            
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)
            
            # await self.log_user_activity(user_id, "registration")  # ❌ Закомментировано для MVP
            
            logger.info(f"Создан новый пользователь: {user_id} ({username})")
            return user
            
        except Exception as e:
            logger.error(f"Ошибка при создании пользователя {user_id}: {e}")
            await self.session.rollback()
            return None
    
    async def update_user_activity(self, user_id: int) -> bool:
        """Обновить время последней активности пользователя"""
        try:
            await self.session.execute(
                update(User)
                .where(User.user_id == user_id)
                .values(last_activity=datetime.now(timezone.utc))
            )
            await self.session.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка при обновлении активности пользователя {user_id}: {e}")
            return False
    
    async def update_user_language(self, user_id: int, language: str) -> bool:
        """Обновить язык пользователя"""
        try:
            await self.session.execute(
                update(User)
                .where(User.user_id == user_id)
                .values(language=language)
            )
            await self.session.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка при обновлении языка пользователя {user_id}: {e}")
            return False
    
    async def update_user_status(self, user_id: int, is_active: bool) -> bool:
        """Обновить статус пользователя"""
        try:
            await self.session.execute(
                update(User)
                .where(User.user_id == user_id)
                .values(is_active=is_active)
            )
            await self.session.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка при обновлении статуса пользователя {user_id}: {e}")
            return False
    
    async def get_or_create_user(
        self, 
        user_id: int, 
        username: Optional[str] = None, 
        full_name: str = "Пользователь"
    ) -> User:
        """Получить существующего пользователя или создать нового"""
        user = await self.get_user_by_telegram_id(user_id)
        
        if not user:
            user = await self.create_user(user_id, username, full_name)
            if not user:
                raise Exception(f"Не удалось создать пользователя {user_id}")
        else:
            # Обновить активность для существующего пользователя
            await self.update_user_activity(user_id)
        
        return user
    
    # ❌ ЗАКОММЕНТИРОВАНО ДЛЯ MVP - детальное логирование активности не нужно для простого бота
    # async def log_user_activity(
    #     self, 
    #     user_id: int, 
    #     action: str, 
    #     lesson_id: Optional[int] = None, 
    #     extra_data: Optional[str] = None
    # ) -> bool:
    #     """Логирование активности пользователя"""
    #     try:
    #         activity = UserActivity(
    #             user_id=user_id,
    #             action=action,
    #             lesson_id=lesson_id,
    #             timestamp=datetime.now(timezone.utc),
    #             extra_data=extra_data
    #         )
    #         
    #         self.session.add(activity)
    #         await self.session.commit()
    #         return True
    #         
    #     except Exception as e:
    #         logger.error(f"Ошибка при логировании активности пользователя {user_id}: {e}")
    #         return False
    
    async def log_user_activity(
        self, 
        user_id: int, 
        action: str, 
        lesson_id: Optional[int] = None, 
        extra_data: Optional[str] = None
    ) -> bool:
        """Заглушка для логирования активности пользователя (для совместимости с существующим кодом)"""
        # В MVP просто логируем в консоль без сохранения в БД
        logger.info(f"User {user_id} action: {action} (lesson: {lesson_id})")
        return True
    
    async def block_user(self, user_id: int) -> bool:
        """Заблокировать пользователя"""
        try:
            await self.session.execute(
                update(User)
                .where(User.user_id == user_id)
                .values(is_active=False)
            )
            await self.session.commit()
            
            # await self.log_user_activity(user_id, "blocked")  # ❌ Закомментировано для MVP
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при блокировке пользователя {user_id}: {e}")
            return False
    
    async def unblock_user(self, user_id: int) -> bool:
        """Разблокировать пользователя"""
        try:
            await self.session.execute(
                update(User)
                .where(User.user_id == user_id)
                .values(is_active=True)
            )
            await self.session.commit()
            
            # await self.log_user_activity(user_id, "unblocked")  # ❌ Закомментировано для MVP
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при разблокировке пользователя {user_id}: {e}")
            return False