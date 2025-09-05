"""
Скрипт для тестирования middleware и поиска проблемы с правами администратора
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
from middlewares.database import DatabaseMiddleware
from middlewares.auth import AuthMiddleware 
from middlewares.admin import AdminMiddleware

# Детальное логирование
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

router = Router()

@router.message(Command("test_admin"))
async def test_admin_access(message: Message, admin, is_admin_db):
    """Тестирование доступа администратора"""
    user_id = message.from_user.id
    
    text = f"""
🔍 <b>Тест прав администратора</b>

👤 <b>Пользователь:</b>
• ID: <code>{user_id}</code>
• Username: @{message.from_user.username or 'Не указан'}

🔐 <b>Права:</b>
• is_admin_db: {is_admin_db}
• admin объект: {admin is not None}

📋 <b>Детали admin:</b>
"""
    
    if admin:
        text += f"""
• ID: {admin.user_id}
• Username: {admin.username}
• Права: {admin.permissions}
• Активен: {admin.is_active}
• Последний вход: {admin.last_login}
"""
    else:
        text += "• Объект admin отсутствует"
    
    await message.answer(text, parse_mode="HTML")

@router.callback_query(F.data == "test_support")
async def test_support_callback(callback: CallbackQuery, admin, is_admin_db):
    """Тестирование callback для поддержки"""
    user_id = callback.from_user.id
    
    logger.info(f"Callback test_support: user_id={user_id}, admin={admin}, is_admin_db={is_admin_db}")
    
    if not is_admin_db or not admin:
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
    
    await callback.answer("✅ Доступ к поддержке разрешен!")
    await callback.message.edit_text(
        f"✅ Тест прошел успешно!\n\nАдмин: {admin.username}\nПрава: {admin.permissions}"
    )

async def main():
    """Запуск тестового бота"""
    await init_db()
    
    bot = Bot(
        token=settings.telegram.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    dp = Dispatcher(storage=MemoryStorage())
    
    # Подключаем middleware в правильном порядке
    dp.message.middleware(DatabaseMiddleware())
    dp.callback_query.middleware(DatabaseMiddleware())
    dp.message.middleware(AuthMiddleware()) 
    dp.callback_query.middleware(AuthMiddleware())
    dp.message.middleware(AdminMiddleware())
    dp.callback_query.middleware(AdminMiddleware())
    
    dp.include_router(router)
    
    await bot.delete_webhook(drop_pending_updates=True)
    
    print("🧪 Тестовый бот запущен")
    print("📝 Команды:")
    print("   /test_admin - проверить права администратора")
    print("   Callback 'test_support' - тест callback")
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("👋 Тестовый бот остановлен")