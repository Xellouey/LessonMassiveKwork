"""
Скрипт для создания администратора в базе данных
"""
import asyncio
import sys
sys.path.insert(0, '.')

from database.database import init_db, get_db_session
from services.admin import AdminService

async def create_admin():
    """Создание администратора"""
    print("🔧 Создание администратора в базе данных...")
    
    # Инициализируем базу данных
    await init_db()
    
    async for session in get_db_session():
        admin_service = AdminService(session)
        
        # Получаем ID администратора из .env (должен совпадать с ADMIN_IDS)
        # Используем реальный Telegram ID пользователя
        admin_user_id = 897676474  # Telegram ID: @dmitriy_mityuk
        
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
                username="dmitriy_mityuk",
                permissions="all"
            )
            
            if admin:
                print(f"✅ Администратор успешно создан!")
                print(f"   ID: {admin.user_id}")
                print(f"   Username: {admin.username}")
                print(f"   Права: {admin.permissions}")
            else:
                print("❌ Ошибка при создании администратора")
        
        break  # Выходим из цикла after first session

if __name__ == "__main__":
    print("🚀 Настройка административного доступа...")
    print()
    print("📝 ВАЖНО: Замените admin_user_id в скрипте на ваш реальный Telegram ID")
    print("   Получить свой ID можно через @userinfobot в Telegram")
    print()
    
    try:
        asyncio.run(create_admin())
        print()
        print("🎉 Готово! Теперь вы можете:")
        print("   1. Запустить бота: python bot.py")
        print("   2. Написать команду /admin в чате с ботом")
        print("   3. Получить доступ к административной панели")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()