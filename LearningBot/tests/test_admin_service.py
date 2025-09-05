"""
Тесты для AdminService
"""
import pytest
from datetime import datetime

from services.admin import AdminService
from database.models import Admin


class TestAdminService:
    """Тесты сервиса администраторов"""
    
    @pytest.mark.asyncio
    async def test_get_admin_by_user_id_not_exists(self, admin_service: AdminService):
        """Тест получения несуществующего администратора"""
        admin = await admin_service.get_admin_by_user_id(999999999)
        assert admin is None
    
    @pytest.mark.asyncio
    async def test_create_admin_success(self, admin_service: AdminService):
        """Тест успешного создания администратора"""
        user_id = 123456789
        username = "test_admin"
        permissions = "all"
        
        admin = await admin_service.create_admin(user_id, username, permissions)
        
        assert admin is not None
        assert admin.user_id == user_id
        assert admin.username == username
        assert admin.permissions == permissions
        assert admin.is_active is True
    
    @pytest.mark.asyncio
    async def test_create_admin_duplicate(self, admin_service: AdminService):
        """Тест создания дублирующегося администратора"""
        user_id = 123456789
        
        # Создаем первого администратора
        admin1 = await admin_service.create_admin(user_id, "admin1")
        assert admin1 is not None
        
        # Пытаемся создать второго с тем же user_id
        admin2 = await admin_service.create_admin(user_id, "admin2")
        assert admin2.id == admin1.id  # Должен вернуть существующего
    
    @pytest.mark.asyncio
    async def test_get_admin_by_user_id_exists(self, admin_service: AdminService):
        """Тест получения существующего администратора"""
        user_id = 987654321
        
        # Создаем администратора
        created_admin = await admin_service.create_admin(user_id, "test_user")
        assert created_admin is not None
        
        # Получаем его
        found_admin = await admin_service.get_admin_by_user_id(user_id)
        assert found_admin is not None
        assert found_admin.id == created_admin.id
        assert found_admin.user_id == user_id
    
    @pytest.mark.asyncio
    async def test_update_admin_permissions(self, admin_service: AdminService):
        """Тест обновления прав администратора"""
        user_id = 555666777
        
        # Создаем администратора
        admin = await admin_service.create_admin(user_id, "test_admin")
        assert admin.permissions == "all"
        
        # Обновляем права
        new_permissions = '["lessons", "users"]'
        success = await admin_service.update_admin_permissions(user_id, new_permissions)
        assert success is True
        
        # Проверяем обновление
        updated_admin = await admin_service.get_admin_by_user_id(user_id)
        assert updated_admin.permissions == new_permissions
    
    @pytest.mark.asyncio
    async def test_set_admin_active_status(self, admin_service: AdminService):
        """Тест активации/деактивации администратора"""
        user_id = 444555666
        
        # Создаем администратора
        admin = await admin_service.create_admin(user_id, "test_admin")
        assert admin.is_active is True
        
        # Деактивируем
        success = await admin_service.set_admin_active(user_id, False)
        assert success is True
        
        # Проверяем деактивацию
        updated_admin = await admin_service.get_admin_by_user_id(user_id)
        assert updated_admin.is_active is False
        
        # Активируем обратно
        success = await admin_service.set_admin_active(user_id, True)
        assert success is True
        
        # Проверяем активацию
        reactivated_admin = await admin_service.get_admin_by_user_id(user_id)
        assert reactivated_admin.is_active is True
    
    @pytest.mark.asyncio
    async def test_delete_admin(self, admin_service: AdminService):
        """Тест удаления администратора"""
        user_id = 333444555
        
        # Создаем администратора
        admin = await admin_service.create_admin(user_id, "test_admin")
        assert admin is not None
        
        # Удаляем
        success = await admin_service.delete_admin(user_id)
        assert success is True
        
        # Проверяем удаление
        deleted_admin = await admin_service.get_admin_by_user_id(user_id)
        assert deleted_admin is None
    
    @pytest.mark.asyncio
    async def test_get_all_admins(self, admin_service: AdminService):
        """Тест получения всех администраторов"""
        # Создаем несколько администраторов
        admin_ids = [111222333, 444555666, 777888999]
        
        for user_id in admin_ids:
            await admin_service.create_admin(user_id, f"admin_{user_id}")
        
        # Получаем всех администраторов
        all_admins = await admin_service.get_all_admins()
        
        # Проверяем, что все созданы
        assert len(all_admins) >= len(admin_ids)
        created_ids = [admin.user_id for admin in all_admins]
        
        for user_id in admin_ids:
            assert user_id in created_ids
    
    @pytest.mark.asyncio
    async def test_check_permission_all(self, admin_service: AdminService):
        """Тест проверки разрешений для администратора с правами 'all'"""
        user_id = 666777888
        
        # Создаем администратора с правами 'all'
        admin = await admin_service.create_admin(user_id, "super_admin", "all")
        assert admin is not None
        
        # Проверяем различные разрешения
        assert await admin_service.check_permission(user_id, "lessons") is True
        assert await admin_service.check_permission(user_id, "users") is True
        assert await admin_service.check_permission(user_id, "broadcasts") is True
        assert await admin_service.check_permission(user_id, "any_permission") is True
    
    @pytest.mark.asyncio
    async def test_check_permission_specific(self, admin_service: AdminService):
        """Тест проверки конкретных разрешений"""
        user_id = 888999000
        
        # Создаем администратора с ограниченными правами
        permissions = '["lessons", "users"]'
        admin = await admin_service.create_admin(user_id, "limited_admin", permissions)
        assert admin is not None
        
        # Проверяем разрешенные действия
        assert await admin_service.check_permission(user_id, "lessons") is True
        assert await admin_service.check_permission(user_id, "users") is True
        
        # Проверяем неразрешенные действия
        assert await admin_service.check_permission(user_id, "broadcasts") is False
        assert await admin_service.check_permission(user_id, "settings") is False
    
    @pytest.mark.asyncio
    async def test_check_permission_inactive_admin(self, admin_service: AdminService):
        """Тест проверки разрешений для неактивного администратора"""
        user_id = 111000111
        
        # Создаем администратора
        admin = await admin_service.create_admin(user_id, "inactive_admin")
        assert admin is not None
        
        # Деактивируем
        await admin_service.set_admin_active(user_id, False)
        
        # Проверяем, что разрешения не работают
        assert await admin_service.check_permission(user_id, "lessons") is False
        assert await admin_service.check_permission(user_id, "any_action") is False
    
    @pytest.mark.asyncio
    async def test_check_permission_nonexistent_admin(self, admin_service: AdminService):
        """Тест проверки разрешений для несуществующего администратора"""
        assert await admin_service.check_permission(999999999, "lessons") is False
    
    @pytest.mark.asyncio
    async def test_update_last_login(self, admin_service: AdminService):
        """Тест обновления времени последнего входа"""
        user_id = 222333444
        
        # Создаем администратора
        admin = await admin_service.create_admin(user_id, "test_admin")
        initial_login = admin.last_login
        
        # Обновляем время входа
        success = await admin_service.update_last_login(user_id)
        assert success is True
        
        # Проверяем обновление
        updated_admin = await admin_service.get_admin_by_user_id(user_id)
        assert updated_admin.last_login != initial_login
        assert updated_admin.last_login is not None