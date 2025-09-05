"""
Временный скрипт для проверки ID пользователя и отладки админ-доступа
"""
import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import settings
from database.database import init_db, get_db_session
from services.admin import AdminService

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = Router()

@router.message(Command("start"))
async def start_command(message: Message):
    """Показать информацию о пользователе"""
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    
    # Проверим, есть ли пользователь в списке админов
    async for session in get_db_session():
        admin_service = AdminService(session)
        admin = await admin_service.get_admin_by_user_id(user_id)
        
        admin_status = "✅ ВЫ АДМИНИСТРАТОР" if admin else "❌ Не администратор"
        
        info_text = f"""
🆔 <b>Информация о вашем аккаунте:</b>

• Telegram ID: <code>{user_id}</code>
• Username: @{username or 'Не указан'}
• Имя: {first_name or 'Не указано'}
• Статус: {admin_status}

📝 <b>Для добавления в админы:</b>
Если вы должны быть администратором, сообщите разработчику ваш ID: <code>{user_id}</code>
"""
        
        await message.answer(info_text, parse_mode="HTML")
        break

@router.message(Command("admin"))
async def admin_command(message: Message):
    """Проверка доступа к админке"""
    user_id = message.from_user.id
    
    async for session in get_db_session():
        admin_service = AdminService(session)
        admin = await admin_service.get_admin_by_user_id(user_id)
        
        if admin:
            await message.answer(f"✅ Вы администратор! Username: {admin.username}, Права: {admin.permissions}")
        else:
            await message.answer(f"❌ Ваш ID {user_id} не найден в списке администраторов")
        break

async def main():
    """Запуск отладочного бота"""
    await init_db()
    
    bot = Bot(
        token=settings.telegram.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    
    await bot.delete_webhook(drop_pending_updates=True)
    
    print("🔍 Debug bot запущен. Отправьте /start для получения вашего ID")
    print("📱 Или /admin для проверки админ-доступа")
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("👋 Debug bot остановлен")