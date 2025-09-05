"""
Middleware для защиты от спама (throttling)
"""
import asyncio
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message


class ThrottlingMiddleware(BaseMiddleware):
    """
    Middleware для ограничения частоты запросов (антиспам)
    """
    
    def __init__(self, rate_limit: float = 0.5):
        """
        :param rate_limit: Минимальный интервал между сообщениями в секундах
        """
        self.rate_limit = rate_limit
        self.user_timeouts: Dict[int, float] = {}
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id if event.from_user else None
        
        if not user_id:
            return await handler(event, data)
        
        # Получение текущего времени
        current_time = asyncio.get_event_loop().time()
        
        # Проверка последнего времени сообщения пользователя
        last_time = self.user_timeouts.get(user_id, 0)
        
        # Если прошло недостаточно времени, игнорируем сообщение
        if current_time - last_time < self.rate_limit:
            return
        
        # Обновление времени последнего сообщения
        self.user_timeouts[user_id] = current_time
        
        return await handler(event, data)