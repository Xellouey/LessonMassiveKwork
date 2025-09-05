"""
Тесты для обработчиков рассылок в админ-панели
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from aiogram.types import CallbackQuery, Message, User as TgUser
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Admin, User, Broadcast
# from database.models import BroadcastDelivery  # ❌ Закомментировано для MVP
from services.broadcast import BroadcastService
from states.admin import BroadcastStates


class TestBroadcastHandlers:
    """Тесты для обработчиков рассылок"""

    @pytest.fixture
    async def mock_callback(self):
        """Фикстура для создания mock CallbackQuery"""
        callback = AsyncMock(spec=CallbackQuery)
        callback.message = AsyncMock(spec=Message)
        callback.from_user = AsyncMock(spec=TgUser)
        callback.from_user.id = 12345  # ID администратора
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        return callback

    @pytest.fixture
    async def mock_message(self):
        """Фикстура для создания mock Message"""
        message = AsyncMock(spec=Message)
        message.from_user = AsyncMock(spec=TgUser)
        message.from_user.id = 12345  # ID администратора
        message.answer = AsyncMock()
        message.delete = AsyncMock()
        return message

    @pytest.fixture
    async def mock_state(self):
        """Фикстура для создания mock FSMContext"""
        state = AsyncMock(spec=FSMContext)
        state.set_state = AsyncMock()
        state.get_state = AsyncMock()
        state.set_data = AsyncMock()
        state.get_data = AsyncMock(return_value={})
        state.clear = AsyncMock()
        return state

    @pytest.fixture
    async def mock_broadcast_service(self):
        """Фикстура для создания mock BroadcastService"""
        service = AsyncMock(spec=BroadcastService)
        return service

    @pytest.fixture
    async def sample_broadcast_data(self):
        """Создание тестовых данных для рассылки"""
        broadcast = Broadcast(
            id=1,
            admin_id=12345,
            text="Тестовая рассылка",
            media_type=None,
            file_id=None,
            status="pending",
            created_at=datetime.now(timezone.utc),
            total_users=0,
            success_count=0
        )
        return broadcast

    async def test_show_broadcasts_menu(self, mock_callback, db_session):
        """Тест отображения меню рассылок"""
        from handlers.admin.broadcast import show_broadcasts_menu
        
        await show_broadcasts_menu(mock_callback)
        
        # Проверяем, что сообщение было отредактировано
        mock_callback.message.edit_text.assert_called_once()
        mock_callback.answer.assert_called_once()
        
        # Проверяем содержание текста
        call_args = mock_callback.message.edit_text.call_args
        assert "📢 Управление рассылками" in call_args[0][0]

    async def test_show_new_broadcast_form(self, mock_callback, mock_state):
        """Тест отображения формы создания новой рассылки"""
        from handlers.admin.broadcast import show_new_broadcast_form
        
        await show_new_broadcast_form(mock_callback, mock_state)
        
        # Проверяем установку состояния
        mock_state.set_state.assert_called_once_with(BroadcastStates.entering_broadcast_text)
        
        # Проверяем отправку сообщения
        mock_callback.message.edit_text.assert_called_once()
        call_args = mock_callback.message.edit_text.call_args
        assert "📝 Введите текст рассылки" in call_args[0][0]

    async def test_handle_broadcast_text_input(self, mock_message, mock_state):
        """Тест обработки текста рассылки"""
        from handlers.admin.broadcast import handle_broadcast_text
        
        mock_message.text = "Привет! Новый урок уже доступен!"
        mock_state.get_data.return_value = {}
        
        await handle_broadcast_text(mock_message, mock_state)
        
        # Проверяем сохранение данных
        mock_state.set_data.assert_called_once()
        saved_data = mock_state.set_data.call_args[0][0]
        assert saved_data['text'] == "Привет! Новый урок уже доступен!"
        
        # Проверяем переход к следующему состоянию
        mock_state.set_state.assert_called_once_with(BroadcastStates.uploading_broadcast_media)

    async def test_handle_media_upload(self, mock_message, mock_state):
        """Тест обработки загрузки медиа"""
        from handlers.admin.broadcast import handle_broadcast_media
        
        # Создаем mock для фото
        mock_message.photo = [MagicMock()]
        mock_message.photo[-1].file_id = "test_photo_id"
        mock_state.get_data.return_value = {'text': 'Тестовый текст'}
        
        await handle_broadcast_media(mock_message, mock_state)
        
        # Проверяем сохранение данных
        mock_state.set_data.assert_called_once()
        saved_data = mock_state.set_data.call_args[0][0]
        assert saved_data['media_type'] == 'photo'
        assert saved_data['file_id'] == 'test_photo_id'
        
        # Проверяем переход к состоянию выбора аудитории
        mock_state.set_state.assert_called_once_with(BroadcastStates.selecting_audience)

    async def test_handle_skip_media(self, mock_callback, mock_state):
        """Тест пропуска загрузки медиа"""
        from handlers.admin.broadcast import skip_media_upload
        
        mock_state.get_data.return_value = {'text': 'Тестовый текст'}
        
        await skip_media_upload(mock_callback, mock_state)
        
        # Проверяем переход к выбору аудитории
        mock_state.set_state.assert_called_once_with(BroadcastStates.selecting_audience)
        
        # Проверяем отображение меню выбора аудитории
        mock_callback.message.edit_text.assert_called_once()

    async def test_select_audience_all(self, mock_callback, mock_state, db_session, mock_broadcast_service):
        """Тест выбора аудитории 'всем пользователям'"""
        from handlers.admin.broadcast import select_audience
        
        mock_callback.data = "broadcast_audience:all"
        mock_state.get_data.return_value = {
            'text': 'Тестовый текст',
            'media_type': None,
            'file_id': None
        }
        
        with patch('handlers.admin.broadcast.BroadcastService') as MockBroadcastService:
            MockBroadcastService.return_value = mock_broadcast_service
            mock_broadcast_service.create_broadcast.return_value = AsyncMock(id=1)
            
            await select_audience(mock_callback, mock_state, db_session)
            
            # Проверяем создание рассылки
            mock_broadcast_service.create_broadcast.assert_called_once_with(
                admin_id=12345,
                text='Тестовый текст',
                media_type=None,
                file_id=None
            )

    async def test_confirm_broadcast_send(self, mock_callback, mock_state, db_session, mock_broadcast_service):
        """Тест подтверждения отправки рассылки"""
        from handlers.admin.broadcast import confirm_broadcast_send
        
        mock_callback.data = "confirm_broadcast:1:all"
        
        with patch('handlers.admin.broadcast.BroadcastService') as MockBroadcastService:
            MockBroadcastService.return_value = mock_broadcast_service
            mock_broadcast_service.send_broadcast.return_value = True
            
            await confirm_broadcast_send(mock_callback, mock_state, db_session)
            
            # Проверяем отправку рассылки
            mock_broadcast_service.send_broadcast.assert_called_once_with(
                broadcast_id=1,
                target_audience="all",
                bot_token=None  # В тестах токен не передается
            )

    async def test_show_broadcasts_history(self, mock_callback, db_session, mock_broadcast_service, sample_broadcast_data):
        """Тест отображения истории рассылок"""
        from handlers.admin.broadcast import show_broadcasts_history
        
        with patch('handlers.admin.broadcast.BroadcastService') as MockBroadcastService:
            MockBroadcastService.return_value = mock_broadcast_service
            mock_broadcast_service.get_broadcasts_history.return_value = [sample_broadcast_data]
            
            await show_broadcasts_history(mock_callback, db_session)
            
            # Проверяем запрос истории
            mock_broadcast_service.get_broadcasts_history.assert_called_once()
            
            # Проверяем отображение результата
            mock_callback.message.edit_text.assert_called_once()
            call_args = mock_callback.message.edit_text.call_args
            assert "📋 История рассылок" in call_args[0][0]

    async def test_show_broadcast_statistics(self, mock_callback, db_session, mock_broadcast_service):
        """Тест отображения статистики рассылки"""
        from handlers.admin.broadcast import show_broadcast_stats
        
        mock_callback.data = "broadcast_stats:1"
        
        mock_stats = {
            'broadcast_id': 1,
            'text': 'Тестовая рассылка',
            'status': 'completed',
            'total_users': 100,
            'success_count': 95,
            'failed_count': 5,
            'success_rate': 95.0,
            'sent_at': datetime.now(timezone.utc)
        }
        
        with patch('handlers.admin.broadcast.BroadcastService') as MockBroadcastService:
            MockBroadcastService.return_value = mock_broadcast_service
            mock_broadcast_service.get_broadcast_statistics.return_value = mock_stats
            
            await show_broadcast_stats(mock_callback, db_session)
            
            # Проверяем запрос статистики
            mock_broadcast_service.get_broadcast_statistics.assert_called_once_with(1)
            
            # Проверяем отображение статистики
            mock_callback.message.edit_text.assert_called_once()
            call_args = mock_callback.message.edit_text.call_args
            text = call_args[0][0]
            assert "📊 Статистика рассылки" in text
            assert "95.0%" in text  # Success rate

    async def test_cancel_broadcast(self, mock_callback, db_session, mock_broadcast_service):
        """Тест отмены рассылки"""
        from handlers.admin.broadcast import cancel_broadcast
        
        mock_callback.data = "cancel_broadcast:1"
        
        with patch('handlers.admin.broadcast.BroadcastService') as MockBroadcastService:
            MockBroadcastService.return_value = mock_broadcast_service
            mock_broadcast_service.cancel_broadcast.return_value = True
            
            await cancel_broadcast(mock_callback, db_session)
            
            # Проверяем отмену рассылки
            mock_broadcast_service.cancel_broadcast.assert_called_once_with(1)
            
            # Проверяем уведомление об успехе
            mock_callback.answer.assert_called_once()
            assert "отменена" in mock_callback.answer.call_args[0][0]

    async def test_delete_broadcast(self, mock_callback, db_session, mock_broadcast_service):
        """Тест удаления рассылки"""
        from handlers.admin.broadcast import delete_broadcast
        
        mock_callback.data = "delete_broadcast:1"
        
        with patch('handlers.admin.broadcast.BroadcastService') as MockBroadcastService:
            MockBroadcastService.return_value = mock_broadcast_service
            mock_broadcast_service.delete_broadcast.return_value = True
            
            await delete_broadcast(mock_callback, db_session)
            
            # Проверяем удаление рассылки
            mock_broadcast_service.delete_broadcast.assert_called_once_with(1)
            
            # Проверяем уведомление об успехе
            mock_callback.answer.assert_called_once()
            assert "удалена" in mock_callback.answer.call_args[0][0]

    async def test_show_active_broadcasts(self, mock_callback, db_session, mock_broadcast_service, sample_broadcast_data):
        """Тест отображения активных рассылок"""
        from handlers.admin.broadcast import show_active_broadcasts
        
        sample_broadcast_data.status = "sending"
        
        with patch('handlers.admin.broadcast.BroadcastService') as MockBroadcastService:
            MockBroadcastService.return_value = mock_broadcast_service
            mock_broadcast_service.get_active_broadcasts.return_value = [sample_broadcast_data]
            
            await show_active_broadcasts(mock_callback, db_session)
            
            # Проверяем запрос активных рассылок
            mock_broadcast_service.get_active_broadcasts.assert_called_once()
            
            # Проверяем отображение результата
            mock_callback.message.edit_text.assert_called_once()
            call_args = mock_callback.message.edit_text.call_args
            assert "⏸️ Активные рассылки" in call_args[0][0]

    async def test_error_handling_in_broadcast_creation(self, mock_callback, mock_state, db_session):
        """Тест обработки ошибок при создании рассылки"""
        from handlers.admin.broadcast import select_audience
        
        mock_callback.data = "broadcast_audience:all"
        mock_state.get_data.return_value = {
            'text': 'Тестовый текст',
            'media_type': None,
            'file_id': None
        }
        
        with patch('handlers.admin.broadcast.BroadcastService') as MockBroadcastService:
            mock_service = AsyncMock()
            mock_service.create_broadcast.side_effect = Exception("Database error")
            MockBroadcastService.return_value = mock_service
            
            await select_audience(mock_callback, mock_state, db_session)
            
            # Проверяем обработку ошибки
            mock_callback.answer.assert_called_once()
            assert "Ошибка" in mock_callback.answer.call_args[0][0]

    async def test_broadcast_text_validation(self, mock_message, mock_state):
        """Тест валидации текста рассылки"""
        from handlers.admin.broadcast import handle_broadcast_text
        
        # Тест слишком длинного текста
        mock_message.text = "А" * 5000  # Слишком длинный текст
        
        await handle_broadcast_text(mock_message, mock_state)
        
        # Проверяем отправку сообщения об ошибке
        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args
        assert "слишком длинный" in call_args[0][0].lower() or "превышает" in call_args[0][0]

    async def test_broadcast_with_video_media(self, mock_message, mock_state):
        """Тест рассылки с видео"""
        from handlers.admin.broadcast import handle_broadcast_media
        
        # Создаем mock для видео
        mock_message.video = MagicMock()
        mock_message.video.file_id = "test_video_id"
        mock_message.photo = None
        mock_message.document = None
        mock_state.get_data.return_value = {'text': 'Тестовый текст с видео'}
        
        await handle_broadcast_media(mock_message, mock_state)
        
        # Проверяем сохранение видео
        mock_state.set_data.assert_called_once()
        saved_data = mock_state.set_data.call_args[0][0]
        assert saved_data['media_type'] == 'video'
        assert saved_data['file_id'] == 'test_video_id'

    async def test_broadcast_with_document_media(self, mock_message, mock_state):
        """Тест рассылки с документом"""
        from handlers.admin.broadcast import handle_broadcast_media
        
        # Создаем mock для документа
        mock_message.document = MagicMock()
        mock_message.document.file_id = "test_document_id"
        mock_message.photo = None
        mock_message.video = None
        mock_state.get_data.return_value = {'text': 'Тестовый текст с документом'}
        
        await handle_broadcast_media(mock_message, mock_state)
        
        # Проверяем сохранение документа
        mock_state.set_data.assert_called_once()
        saved_data = mock_state.set_data.call_args[0][0]
        assert saved_data['media_type'] == 'document'
        assert saved_data['file_id'] == 'test_document_id'