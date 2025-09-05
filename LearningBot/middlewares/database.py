"""
Middleware для предоставления доступа к сессии базы данных
"""
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from database.database import get_db_session


class DatabaseMiddleware(BaseMiddleware):
    """
    Middleware для предоставления сессии базы данных в handlers
    """
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        # Создание сессии базы данных
        async for session in get_db_session():
            data['session'] = session
            try:
                return await handler(event, data)
            finally:
                # Сессия автоматически закроется в get_db_session()
                pass