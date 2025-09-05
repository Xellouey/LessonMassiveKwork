"""
Обновление username для администратора 494482943
"""
import asyncio
import sys
sys.path.insert(0, '.')

from database.database import init_db, get_db_session
from services.admin import AdminService
from sqlalchemy import update
from database.models import Admin

async def update_username():
    """Обновление username администратора"""
    print("🔧 Обновление username администратора 494482943...")
    
    await init_db()
    
    async for session in get_db_session():
        # Обновляем username напрямую в базе
        await session.execute(
            update(Admin)
            .where(Admin.user_id == 494482943)
            .values(username="egorbannikov")
        )
        await session.commit()
        
        print("✅ Username обновлен!")
        
        # Проверяем результат
        admin_service = AdminService(session)
        admin = await admin_service.get_admin_by_user_id(494482943)
        
        if admin:
            print(f"📋 Данные администратора:")
            print(f"   ID: {admin.user_id}")
            print(f"   Username: @{admin.username}")
            print(f"   Права: {admin.permissions}")
            print(f"   Активен: {admin.is_active}")
        
        break

if __name__ == "__main__":
    asyncio.run(update_username())