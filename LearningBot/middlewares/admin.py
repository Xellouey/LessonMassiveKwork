"""
Middleware для административных функций
"""
import logging
from typing import Callable, Dict, Any, Awaitable
from functools import wraps
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Admin
from sqlalchemy import select

logger = logging.getLogger(__name__)


class AdminMiddleware(BaseMiddleware):
    """
    Middleware для проверки административных прав пользователя
    """
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Получаем ID пользователя
        user_id = getattr(event, 'from_user', None)
        user_id = getattr(user_id, 'id', None) if user_id else None
        
        if not user_id:
            return await handler(event, data)
        
        # Получаем сессию БД
        session: AsyncSession = data.get('session')
        
        if session:
            # Проверяем, является ли пользователь администратором в БД
            result = await session.execute(
                select(Admin).where(
                    Admin.user_id == user_id,
                    Admin.is_active == True
                )
            )
            admin = result.scalar_one_or_none()
            
            # Добавляем информацию об администраторе в данные
            data['admin'] = admin
            data['is_admin_db'] = admin is not None
            
            if admin:
                # Обновляем время последнего входа
                from datetime import datetime
                admin.last_login = datetime.utcnow()
                await session.commit()
        
        return await handler(event, data)


class AdminOnlyMiddleware(BaseMiddleware):
    """
    Middleware который блокирует доступ для не-администраторов
    Используется для административных роутеров
    """
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Проверяем права администратора
        admin = data.get('admin')
        is_admin_db = data.get('is_admin_db', False)
        
        # Логирование для отладки
        user_id = getattr(event, 'from_user', None)
        user_id = getattr(user_id, 'id', None) if user_id else None
        logger.debug(f"AdminOnlyMiddleware: user_id={user_id}, is_admin_db={is_admin_db}, admin={admin}")
        
        if not is_admin_db or not admin:
            # Отправляем сообщение о недостатке прав
            if isinstance(event, Message):
                await event.answer("❌ У вас нет прав администратора для выполнения этого действия.")
            elif isinstance(event, CallbackQuery):
                await event.answer("❌ Недостаточно прав для выполнения действия.", show_alert=True)
            return
        
        return await handler(event, data)


def admin_required(func):
    """Декоратор для проверки административных прав"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Ищем callback или message в аргументах
        event = None
        for arg in args:
            if isinstance(arg, (Message, CallbackQuery)):
                event = arg
                break
        
        if not event:
            # Если не найден event, выполняем функцию как есть
            return await func(*args, **kwargs)
        
        # Проверяем, есть ли в kwargs информация об администраторе
        is_admin_db = kwargs.get('is_admin_db', False)
        admin = kwargs.get('admin')
        
        if not is_admin_db and not admin:
            # Отправляем сообщение о недостатке прав
            if isinstance(event, Message):
                await event.answer("❌ У вас нет прав администратора для выполнения этого действия.")
            elif isinstance(event, CallbackQuery):
                await event.answer("❌ Недостаточно прав для выполнения действия.", show_alert=True)
            return
        
        return await func(*args, **kwargs)
    return wrapper