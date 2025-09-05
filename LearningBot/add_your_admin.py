"""
Скрипт для добавления вашего ID в администраторы
Замените YOUR_TELEGRAM_ID на ваш реальный ID
"""
import asyncio
import sys
sys.path.insert(0, '.')

from database.database import init_db, get_db_session
from services.admin import AdminService

async def add_admin():
    """Добавление администратора"""
    # ЗАМЕНИТЕ ЭТО ЗНАЧЕНИЕ на ваш реальный Telegram ID
    YOUR_TELEGRAM_ID = 123456789  # ❗ ИЗМЕНИТЕ НА ВАШ РЕАЛЬНЫЙ ID
    YOUR_USERNAME = "your_username"  # ❗ ИЗМЕНИТЕ НА ВАШ USERNAME (без @)
    
    print(f"🔧 Добавление администратора {YOUR_TELEGRAM_ID}...")
    
    # Инициализируем базу данных
    await init_db()
    
    async for session in get_db_session():
        admin_service = AdminService(session)
        
        # Проверяем, существует ли уже администратор
        existing_admin = await admin_service.get_admin_by_user_id(YOUR_TELEGRAM_ID)
        
        if existing_admin:
            print(f"✅ Администратор с ID {YOUR_TELEGRAM_ID} уже существует!")
            print(f"   Username: {existing_admin.username}")
            print(f"   Права: {existing_admin.permissions}")
            print(f"   Статус: {'Активен' if existing_admin.is_active else 'Неактивен'}")
        else:
            # Создаем нового администратора
            admin = await admin_service.create_admin(
                user_id=YOUR_TELEGRAM_ID,
                username=YOUR_USERNAME,
                permissions="all"
            )
            
            if admin:
                print(f"✅ Администратор успешно создан!")
                print(f"   ID: {admin.user_id}")
                print(f"   Username: {admin.username}")
                print(f"   Права: {admin.permissions}")
            else:
                print("❌ Ошибка при создании администратора")
        
        break

if __name__ == "__main__":
    try:
        asyncio.run(add_admin())
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()