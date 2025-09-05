"""
Middleware для аутентификации пользователей и администраторов
"""
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from config import settings


class AuthMiddleware(BaseMiddleware):
    """
    Middleware для определения роли пользователя (обычный пользователь или админ)
    """
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        # Определение ID пользователя
        user_id = event.from_user.id if event.from_user else None
        
        if not user_id:
            return await handler(event, data)
        
        # Проверка, является ли пользователь администратором
        is_admin = user_id in settings.telegram.admin_ids
        
        # Добавление информации об аутентификации в данные
        data['is_admin'] = is_admin
        data['user_id'] = user_id
        data['username'] = event.from_user.username if event.from_user else None
        data['full_name'] = event.from_user.full_name if event.from_user else None
        
        return await handler(event, data)