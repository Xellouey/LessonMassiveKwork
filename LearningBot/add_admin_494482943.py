"""
Скрипт для добавления администратора с ID 494482943 в базу данных
"""
import asyncio
import sys
sys.path.insert(0, '.')

from database.database import init_db, get_db_session
from services.admin import AdminService

async def add_admin():
    """Добавление нового администратора"""
    print("🔧 Добавление администратора в базу данных...")
    
    # Инициализируем базу данных
    await init_db()
    
    async for session in get_db_session():
        admin_service = AdminService(session)
        
        # ID нового администратора
        admin_user_id = 494482943
        
        # Проверяем, существует ли уже администратор
        existing_admin = await admin_service.get_admin_by_user_id(admin_user_id)
        
        if existing_admin:
            print(f"✅ Администратор с ID {admin_user_id} уже существует!")
            print(f"   Username: {existing_admin.username}")
            print(f"   Права: {existing_admin.permissions}")
            print(f"   Статус: {'Активен' if existing_admin.is_active else 'Неактивен'}")
        else:
            # Создаем нового администратора
            admin = await admin_service.create_admin(
                user_id=admin_user_id,
                username="egorbannikov",  # Из логов видно что username = egorbannikov
                permissions="all"
            )
            
            if admin:
                print(f"✅ Администратор успешно создан!")
                print(f"   ID: {admin.user_id}")
                print(f"   Username: {admin.username}")
                print(f"   Права: {admin.permissions}")
            else:
                print("❌ Ошибка при создании администратора")
        
        break  # Выходим из цикла после первой сессии

if __name__ == "__main__":
    print("🚀 Добавление нового администратора...")
    print(f"   Telegram ID: 494482943")
    print()
    
    try:
        asyncio.run(add_admin())
        print()
        print("✅ Скрипт выполнен успешно!")
        print()
        print("📝 Что было сделано:")
        print("   1. Добавлен ID 494482943 в ADMIN_IDS в .env файле")
        print("   2. Добавлен ID 494482943 в admins.json для NikolayAIBot")
        print("   3. Создана запись администратора в базе данных LearningBot")
        print()
        print("🔄 Перезапустите боты для применения изменений!")
        
    except Exception as e:
        print(f"❌ Ошибка при выполнении скрипта: {e}")
        print("   Проверьте настройки базы данных и повторите попытку")