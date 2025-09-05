"""
Comprehensive tests for admin lesson handlers with FSM workflows
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from aiogram.types import CallbackQuery, Message, User as TgUser
from aiogram.fsm.context import FSMContext

from handlers.admin.lessons import (
    show_lessons_list,
    navigate_lessons_pages,
    edit_lesson_menu,
    start_lesson_creation,
    start_lesson_deletion,
    confirm_lesson_deletion,
    execute_soft_delete,
    execute_hard_delete,
    execute_force_delete
)
from states.admin import LessonManagementStates
from database.models import Lesson, Purchase, User


class TestAdminLessonHandlers:
    """Tests for admin lesson handlers"""
    
    def create_mock_callback(self, data: str, user_id: int = 12345):
        """Create mock callback query"""
        callback = MagicMock(spec=CallbackQuery)
        callback.data = data
        callback.from_user = MagicMock(spec=TgUser)
        callback.from_user.id = user_id
        callback.message = MagicMock()
        callback.message.edit_text = AsyncMock()
        callback.answer = AsyncMock()
        return callback
    
    def create_mock_message(self, text: str, user_id: int = 12345):
        """Create mock message"""
        message = MagicMock(spec=Message)
        message.text = text
        message.from_user = MagicMock(spec=TgUser)
        message.from_user.id = user_id
        message.answer = AsyncMock()
        return message
    
    @pytest.mark.asyncio
    async def test_show_lessons_list_with_lessons(self, db_session, sample_lesson):
        """Test showing lessons list when lessons exist"""
        callback = self.create_mock_callback("admin_lessons_list")
        
        await show_lessons_list(callback, db_session)
        
        # Verify that edit_text was called
        callback.message.edit_text.assert_called_once()
        callback.answer.assert_called_once()
        
        # Check that the text contains lesson information
        call_args = callback.message.edit_text.call_args[0][0]
        assert "Список всех уроков" in call_args
    
    @pytest.mark.asyncio
    async def test_show_lessons_list_empty(self, db_session):
        """Test showing lessons list when no lessons exist"""
        callback = self.create_mock_callback("admin_lessons_list")
        
        await show_lessons_list(callback, db_session)
        
        callback.message.edit_text.assert_called_once()
        call_args = callback.message.edit_text.call_args[0][0]
        assert "Список уроков пуст" in call_args
    
    @pytest.mark.asyncio
    async def test_edit_lesson_menu_existing_lesson(self, db_session, sample_lesson):
        """Test editing menu for existing lesson"""
        callback = self.create_mock_callback(f"admin_edit_lesson:{sample_lesson.id}")
        
        await edit_lesson_menu(callback, db_session)
        
        callback.message.edit_text.assert_called_once()
        callback.answer.assert_called_once()
        
        call_args = callback.message.edit_text.call_args[0][0]
        assert "Редактирование урока" in call_args
        assert sample_lesson.title in call_args
    
    @pytest.mark.asyncio
    async def test_edit_lesson_menu_nonexistent(self, db_session):
        """Test editing menu for non-existent lesson"""
        callback = self.create_mock_callback("admin_edit_lesson:999999")
        
        await edit_lesson_menu(callback, db_session)
        
        callback.answer.assert_called_once_with("❌ Урок не найден")
    
    @pytest.mark.asyncio
    async def test_start_lesson_creation(self):
        """Test starting lesson creation workflow"""
        callback = self.create_mock_callback("admin_create_lesson")
        state = AsyncMock(spec=FSMContext)
        
        await start_lesson_creation(callback, state)
        
        # Verify FSM state is set
        state.set_state.assert_called_once_with(LessonManagementStates.creating_lesson)
        state.update_data.assert_called_once_with(step="title")
        
        callback.message.edit_text.assert_called_once()
        callback.answer.assert_called_once()
        
        call_args = callback.message.edit_text.call_args[0][0]
        assert "Создание нового урока" in call_args
        assert "Шаг 1 из 6" in call_args
    
    @pytest.mark.asyncio
    async def test_start_lesson_deletion_with_lessons(self, db_session, sample_lesson):
        """Test starting lesson deletion with existing lessons"""
        callback = self.create_mock_callback("admin_delete_lesson")
        state = AsyncMock(spec=FSMContext)
        
        await start_lesson_deletion(callback, db_session, state)
        
        # Verify FSM state is set
        state.set_state.assert_called_once_with(LessonManagementStates.deleting_lesson)
        
        callback.message.edit_text.assert_called_once()
        callback.answer.assert_called_once()
        
        call_args = callback.message.edit_text.call_args[0][0]
        assert "Удаление урока" in call_args
    
    @pytest.mark.asyncio
    async def test_start_lesson_deletion_no_lessons(self, db_session):
        """Test starting lesson deletion with no lessons"""
        callback = self.create_mock_callback("admin_delete_lesson")
        state = AsyncMock(spec=FSMContext)
        
        await start_lesson_deletion(callback, db_session, state)
        
        callback.message.edit_text.assert_called_once()
        call_args = callback.message.edit_text.call_args[0][0]
        assert "Уроки не найдены" in call_args
    
    @pytest.mark.asyncio
    async def test_confirm_lesson_deletion_safe_lesson(self, db_session):
        """Test confirming deletion for lesson without purchases"""
        # Create lesson without purchases
        lesson = Lesson(
            title="Safe to delete",
            description="Test lesson",
            price_stars=100,
            content_type="text",
            is_active=True,
            is_free=False,
            category="Test"
        )
        db_session.add(lesson)
        await db_session.commit()
        await db_session.refresh(lesson)
        
        callback = self.create_mock_callback(f"admin_confirm_delete:{lesson.id}")
        state = AsyncMock(spec=FSMContext)
        
        await confirm_lesson_deletion(callback, db_session, state)
        
        # Verify FSM state is set
        state.set_state.assert_called_once_with(LessonManagementStates.confirming_lesson_deletion)
        state.update_data.assert_called_once_with(deleting_lesson_id=lesson.id)
        
        callback.message.edit_text.assert_called_once()
        callback.answer.assert_called_once()
        
        call_args = callback.message.edit_text.call_args[0][0]
        assert "Подтверждение удаления урока" in call_args
        assert "можно безопасно удалить" in call_args
    
    @pytest.mark.asyncio
    async def test_confirm_lesson_deletion_with_purchases(self, db_session, sample_lesson, sample_purchase):
        """Test confirming deletion for lesson with purchases"""
        callback = self.create_mock_callback(f"admin_confirm_delete:{sample_lesson.id}")
        state = AsyncMock(spec=FSMContext)
        
        await confirm_lesson_deletion(callback, db_session, state)
        
        callback.message.edit_text.assert_called_once()
        call_args = callback.message.edit_text.call_args[0][0]
        assert "Ограничения удаления" in call_args
        assert "покупки" in call_args
    
    @pytest.mark.asyncio
    async def test_execute_soft_delete_success(self, db_session):
        """Test successful soft delete execution"""
        # Create lesson for soft deletion
        lesson = Lesson(
            title="For soft delete",
            description="Test lesson",
            price_stars=100,
            content_type="text",
            is_active=True,
            is_free=False,
            category="Test"
        )
        db_session.add(lesson)
        await db_session.commit()
        await db_session.refresh(lesson)
        
        callback = self.create_mock_callback(f"soft_delete:{lesson.id}")
        state = AsyncMock(spec=FSMContext)
        
        await execute_soft_delete(callback, db_session, state)
        
        callback.message.edit_text.assert_called_once()
        callback.answer.assert_called_once()
        state.clear.assert_called_once()
        
        # Verify lesson was deactivated
        from services.lesson import LessonService
        lesson_service = LessonService(db_session)
        updated_lesson = await lesson_service.get_lesson_by_id(lesson.id, include_inactive=True)
        assert updated_lesson.is_active is False
        
        call_args = callback.message.edit_text.call_args[0][0]
        assert "Мягкое удаление выполнено" in call_args
    
    @pytest.mark.asyncio
    async def test_execute_soft_delete_nonexistent(self, db_session):
        """Test soft delete of non-existent lesson"""
        callback = self.create_mock_callback("soft_delete:999999")
        state = AsyncMock(spec=FSMContext)
        
        await execute_soft_delete(callback, db_session, state)
        
        callback.answer.assert_called_once_with("❌ Урок не найден")
    
    @pytest.mark.asyncio
    async def test_execute_hard_delete_success(self, db_session):
        """Test successful hard delete execution"""
        # Create lesson for hard deletion
        lesson = Lesson(
            title="For hard delete",
            description="Test lesson",
            price_stars=100,
            content_type="text",
            is_active=True,
            is_free=False,
            category="Test"
        )
        db_session.add(lesson)
        await db_session.commit()
        await db_session.refresh(lesson)
        lesson_id = lesson.id
        
        callback = self.create_mock_callback(f"hard_delete:{lesson_id}")
        state = AsyncMock(spec=FSMContext)
        
        await execute_hard_delete(callback, db_session, state)
        
        callback.message.edit_text.assert_called_once()
        callback.answer.assert_called_once()
        state.clear.assert_called_once()
        
        # Verify lesson was deleted
        from services.lesson import LessonService
        lesson_service = LessonService(db_session)
        deleted_lesson = await lesson_service.get_lesson_by_id(lesson_id, include_inactive=True)
        assert deleted_lesson is None
        
        call_args = callback.message.edit_text.call_args[0][0]
        assert "Жесткое удаление выполнено" in call_args
    
    @pytest.mark.asyncio
    async def test_execute_force_delete_with_purchases(self, db_session):
        """Test force delete execution with purchases"""
        from database.models import User
        
        # Create lesson, user and purchase
        lesson = Lesson(
            title="Force delete test",
            description="Test lesson",
            price_stars=200,
            content_type="text",
            is_active=True,
            is_free=False,
            category="Test"
        )
        
        user = User(
            user_id=555555,
            username="force_test_user",
            first_name="Test",
            registration_date=datetime.utcnow()
        )
        
        db_session.add(lesson)
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(lesson)
        await db_session.refresh(user)
        
        purchase = Purchase(
            user_id=user.user_id,
            lesson_id=lesson.id,
            amount_stars=lesson.price_stars,
            status="completed",
            purchase_date=datetime.utcnow()
        )
        
        db_session.add(purchase)
        await db_session.commit()
        lesson_id = lesson.id
        
        callback = self.create_mock_callback(f"force_delete:{lesson_id}")
        state = AsyncMock(spec=FSMContext)
        
        await execute_force_delete(callback, db_session, state)
        
        callback.message.edit_text.assert_called_once()
        callback.answer.assert_called_once()
        state.clear.assert_called_once()
        
        # Verify lesson was deleted
        from services.lesson import LessonService
        lesson_service = LessonService(db_session)
        deleted_lesson = await lesson_service.get_lesson_by_id(lesson_id, include_inactive=True)
        assert deleted_lesson is None
        
        call_args = callback.message.edit_text.call_args[0][0]
        assert "Принудительное удаление выполнено" in call_args


class TestAdminLessonHandlersIntegration:
    """Integration tests for admin lesson handlers workflows"""
    
    @pytest.mark.asyncio
    async def test_complete_lesson_creation_workflow(self, db_session):
        """Test complete lesson creation workflow"""
        # This would test the full FSM workflow from start to finish
        # Implementation depends on more complex FSM testing setup
        pass
    
    @pytest.mark.asyncio
    async def test_complete_lesson_deletion_workflow(self, db_session):
        """Test complete lesson deletion workflow"""  
        # This would test the full deletion workflow
        # Implementation depends on more complex FSM testing setup
        pass
    
    @pytest.mark.asyncio
    async def test_lesson_editing_workflow(self, db_session, sample_lesson):
        """Test lesson editing workflow"""
        # This would test the editing workflow
        pass