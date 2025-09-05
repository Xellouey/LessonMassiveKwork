"""
Скрипт для проверки администраторов в базе данных
"""
import asyncio
import sys
sys.path.insert(0, '.')

from database.database import init_db, get_db_session
from services.admin import AdminService

async def check_admins():
    """Проверка администраторов в базе"""
    print("🔍 Проверка администраторов в базе данных...")
    
    # Инициализируем базу данных
    await init_db()
    
    async for session in get_db_session():
        admin_service = AdminService(session)
        
        # Получаем всех администраторов
        admins = await admin_service.get_all_admins()
        
        if not admins:
            print("❌ В базе данных нет администраторов!")
            print("\n📝 Для создания администратора:")
            print("   1. Узнайте свой Telegram ID через @userinfobot")
            print("   2. Отредактируйте create_admin.py")
            print("   3. Запустите: python create_admin.py")
        else:
            print(f"✅ Найдено администраторов: {len(admins)}")
            print("\n👥 Список администраторов:")
            for admin in admins:
                status = "✅ Активен" if admin.is_active else "❌ Неактивен"
                print(f"   • ID: {admin.user_id}")
                print(f"     Username: @{admin.username or 'Не указан'}")
                print(f"     Права: {admin.permissions}")
                print(f"     Статус: {status}")
                print(f"     Последний вход: {admin.last_login or 'Никогда'}")
                print()
        
        break

if __name__ == "__main__":
    try:
        asyncio.run(check_admins())
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()