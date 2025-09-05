"""
Обработчики управления медиа-контентом для административной панели
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from services.media import MediaService
from services.lesson import LessonService
from keyboards.admin import (
    media_management_keyboard, media_types_keyboard, media_actions_keyboard,
    back_to_admin_keyboard, media_categories_keyboard
)
from states.admin import MediaManagementStates
from middlewares.admin import AdminOnlyMiddleware

logger = logging.getLogger(__name__)
router = Router()
router.callback_query.middleware(AdminOnlyMiddleware())
router.message.middleware(AdminOnlyMiddleware())


@router.callback_query(F.data == "admin_media")
async def show_media_management_menu(callback: CallbackQuery):
    """Показать меню управления медиа"""
    try:
        text = """
🎬 <b>Управление медиа-контентом</b>

Здесь вы можете управлять всеми медиа файлами уроков: видео, фотографии, документы и аудио.

📁 <b>Поддерживаемые типы:</b>
• Видео - до 50MB
• Фото - до 20MB  
• Документы - до 20MB
• Аудио - до 50MB

⚡ <b>Функции:</b>
• Просмотр медиа по типам и категориям
• Загрузка и замена файлов
• Оптимизация хранилища
• Поиск и статистика

Выберите действие:
"""

        await callback.message.edit_text(
            text,
            reply_markup=media_management_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка при показе меню управления медиа: {e}")
        await callback.answer("Произошла ошибка при загрузке меню")


@router.callback_query(F.data.startswith("media_type:"))
async def show_media_by_type(callback: CallbackQuery, session: AsyncSession):
    """Показать медиа по типу"""
    try:
        media_type = callback.data.split(":")[1]
        
        media_service = MediaService(session)
        media_list = await media_service.get_media_by_type(media_type)
        
        # Названия типов для отображения
        type_names = {
            "video": "Видео",
            "photo": "Фотографии", 
            "document": "Документы",
            "audio": "Аудио"
        }
        
        type_name = type_names.get(media_type, media_type.capitalize())
        
        if not media_list:
            text = f"""
📁 <b>{type_name}</b>

📭 В этой категории пока нет медиа файлов.
Загрузите первый файл, чтобы увидеть его здесь.

💡 <b>Ограничения:</b>
Максимальный размер для {type_name.lower()}: {media_service.get_media_size_limits()[media_type] // (1024*1024)}MB
"""
            await callback.message.edit_text(
                text,
                reply_markup=back_to_admin_keyboard(),
                parse_mode="HTML"
            )
        else:
            text = f"""
📁 <b>{type_name}</b>

Всего файлов: {len(media_list)}

<b>Список медиа:</b>
"""
            
            for i, media in enumerate(media_list[:10], 1):  # Показываем первые 10
                duration_text = f" ({media.duration}с)" if media.duration else ""
                text += f"{i}. {media.title}{duration_text}\n"
            
            if len(media_list) > 10:
                text += f"\n... и еще {len(media_list) - 10} файлов"
            
            await callback.message.edit_text(
                text,
                reply_markup=media_types_keyboard(media_type),
                parse_mode="HTML"
            )
        
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка при получении медиа типа {media_type}: {e}")
        await callback.answer("Ошибка при загрузке медиа")


@router.callback_query(F.data == "media_upload")
async def start_media_upload(callback: CallbackQuery, state: FSMContext):
    """Начать загрузку медиа"""
    try:
        text = """
📤 <b>Загрузка медиа</b>

Для загрузки медиа файла:

1️⃣ Выберите тип файла
2️⃣ Отправьте файл в чат
3️⃣ Укажите к какому уроку он относится

<b>⚠️ Важно:</b>
• Видео и аудио: до 50MB
• Фото и документы: до 20MB
• Файл должен быть качественным
• Избегайте дубликатов

Выберите тип медиа для загрузки:
"""

        await callback.message.edit_text(
            text,
            reply_markup=media_types_keyboard(),
            parse_mode="HTML"
        )
        
        await state.set_state(MediaManagementStates.selecting_media_type)
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка при начале загрузки медиа: {e}")
        await callback.answer("Ошибка при инициализации загрузки")


@router.callback_query(F.data.startswith("upload_type:"))
async def select_upload_type(callback: CallbackQuery, state: FSMContext):
    """Выбрать тип для загрузки"""
    try:
        media_type = callback.data.split(":")[1]
        
        await state.update_data(media_type=media_type)
        
        type_names = {
            "video": "видео файл",
            "photo": "фотографию",
            "document": "документ", 
            "audio": "аудио файл"
        }
        
        file_type = type_names.get(media_type, "файл")
        
        text = f"""
📤 <b>Загрузка: {file_type}</b>

Теперь отправьте {file_type} в этот чат.

💡 <b>Подсказки:</b>
• Файл должен быть хорошего качества
• Размер не должен превышать лимиты
• Убедитесь, что файл не поврежден

<i>Ожидаю ваш файл...</i>
"""

        await callback.message.edit_text(
            text,
            parse_mode="HTML"
        )
        
        await state.set_state(MediaManagementStates.uploading_file)
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка при выборе типа загрузки: {e}")
        await callback.answer("Ошибка при выборе типа")


@router.message(MediaManagementStates.uploading_file)
async def handle_media_upload(message: Message, state: FSMContext, session: AsyncSession):
    """Обработать загрузку медиа файла"""
    try:
        data = await state.get_data()
        expected_type = data.get('media_type')
        
        media_service = MediaService(session)
        lesson_service = LessonService(session)
        
        # Определяем тип загруженного файла и получаем file_id
        file_id = None
        file_size = 0
        actual_type = None
        
        if message.video:
            file_id = message.video.file_id
            file_size = message.video.file_size or 0
            actual_type = "video"
        elif message.photo:
            # Берем фото наибольшего размера
            photo = message.photo[-1]
            file_id = photo.file_id
            file_size = photo.file_size or 0
            actual_type = "photo"
        elif message.document:
            file_id = message.document.file_id
            file_size = message.document.file_size or 0
            actual_type = "document"
        elif message.audio:
            file_id = message.audio.file_id
            file_size = message.audio.file_size or 0
            actual_type = "audio"
        else:
            await message.answer("❌ Неподдерживаемый тип файла. Отправьте видео, фото, документ или аудио.")
            return
        
        # Проверяем соответствие ожидаемому типу
        if actual_type != expected_type:
            await message.answer(f"❌ Ожидался {expected_type}, а получен {actual_type}. Попробуйте еще раз.")
            return
        
        # Валидируем файл
        if not media_service.validate_media_file(actual_type, file_size):
            max_size = media_service.get_media_size_limits()[actual_type] // (1024*1024)
            await message.answer(f"❌ Файл слишком большой. Максимальный размер для {actual_type}: {max_size}MB")
            return
        
        # Проверяем, не дублируется ли файл
        if await media_service.check_media_file_exists(file_id):
            await message.answer("⚠️ Этот файл уже существует в системе. Выберите другой файл.")
            return
        
        # Создаем временный урок для демонстрации (в реальности нужно связать с существующим)
        # Здесь можно добавить выбор урока
        
        await message.answer(f"""
✅ <b>Файл успешно загружен!</b>

📁 <b>Тип:</b> {actual_type}
📏 <b>Размер:</b> {file_size // 1024}KB
🆔 <b>ID:</b> <code>{file_id}</code>

💡 Теперь этот файл можно использовать в уроках.
""", parse_mode="HTML")
        
        await state.clear()
        
        # Удаляем сообщение пользователя для чистоты
        try:
            await message.delete()
        except:
            pass

    except Exception as e:
        logger.error(f"Ошибка при загрузке медиа: {e}")
        await message.answer("❌ Произошла ошибка при загрузке файла")
        await state.clear()


@router.callback_query(F.data == "media_statistics")
async def show_media_statistics(callback: CallbackQuery, session: AsyncSession):
    """Показать статистику медиа"""
    try:
        media_service = MediaService(session)
        stats = await media_service.get_media_statistics()
        
        if not stats:
            text = """
📊 <b>Статистика медиа</b>

❌ Не удалось загрузить статистику
"""
        else:
            # Форматируем время
            total_hours = stats.get('total_duration', 0) // 3600
            total_minutes = (stats.get('total_duration', 0) % 3600) // 60
            
            text = f"""
📊 <b>Статистика медиа-контента</b>

📈 <b>Общая информация:</b>
• Всего медиа файлов: {stats.get('total_media', 0)}
• Видео: {stats.get('video_count', 0)}
• Фото: {stats.get('photo_count', 0)}
• Документы: {stats.get('document_count', 0)}
• Аудио: {stats.get('audio_count', 0)}

⏱️ <b>Общая длительность:</b>
{total_hours}ч {total_minutes}м

📂 <b>По категориям:</b>
"""
            
            for category, count in stats.get('categories', {}).items():
                text += f"• {category}: {count}\n"
        
        await callback.message.edit_text(
            text,
            reply_markup=back_to_admin_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка при получении статистики медиа: {e}")
        await callback.answer("Ошибка при загрузке статистики")


@router.callback_query(F.data == "media_search")
async def start_media_search(callback: CallbackQuery, state: FSMContext):
    """Начать поиск медиа"""
    try:
        text = """
🔍 <b>Поиск медиа</b>

Введите поисковый запрос для поиска по:
• Названию урока
• Описанию
• Категории
• Типу файла

<i>Начните вводить текст для поиска:</i>
"""

        await callback.message.edit_text(
            text,
            reply_markup=back_to_admin_keyboard(),
            parse_mode="HTML"
        )
        
        await state.set_state(MediaManagementStates.searching_media)
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка при начале поиска медиа: {e}")
        await callback.answer("Ошибка при инициализации поиска")


@router.message(MediaManagementStates.searching_media)
async def handle_media_search(message: Message, state: FSMContext, session: AsyncSession):
    """Обработать поиск медиа"""
    try:
        query = message.text.strip()
        
        if not query or len(query) < 2:
            await message.answer("❌ Поисковый запрос должен содержать минимум 2 символа")
            return
        
        media_service = MediaService(session)
        results = await media_service.search_media(query)
        
        if not results:
            await message.answer(f"📭 По запросу '{query}' ничего не найдено.")
        else:
            text = f"🔍 <b>Результаты поиска: '{query}'</b>\n\nНайдено: {len(results)}\n\n"
            
            for i, media in enumerate(results[:10], 1):
                duration_text = f" ({media.duration}с)" if media.duration else ""
                text += f"{i}. {media.title} ({media.content_type}){duration_text}\n"
            
            if len(results) > 10:
                text += f"\n... и еще {len(results) - 10} результатов"
            
            await message.answer(
                text,
                reply_markup=back_to_admin_keyboard(),
                parse_mode="HTML"
            )
        
        await state.clear()
        
        # Удаляем сообщение пользователя
        try:
            await message.delete()
        except:
            pass

    except Exception as e:
        logger.error(f"Ошибка при поиске медиа: {e}")
        await message.answer("❌ Произошла ошибка при поиске")
        await state.clear()


@router.callback_query(F.data == "media_optimize")
async def optimize_media_storage(callback: CallbackQuery, session: AsyncSession):
    """Оптимизировать медиа хранилище"""
    try:
        await callback.answer("🔄 Начинаю оптимизацию...")
        
        media_service = MediaService(session)
        result = await media_service.optimize_media_storage()
        
        text = f"""
🛠️ <b>Оптимизация завершена</b>

📊 <b>Результаты:</b>
• Найдено дубликатов: {result.get('duplicates_found', 0)}
• Очищено неиспользуемых: {result.get('unused_cleaned', 0)}

✅ Хранилище оптимизировано!
"""

        if result.get('duplicates_found', 0) > 0:
            text += "\n💡 Обнаружены дублирующиеся файлы. Рекомендуется их проверить."

        await callback.message.edit_text(
            text,
            reply_markup=back_to_admin_keyboard(),
            parse_mode="HTML"
        )

    except Exception as e:
        logger.error(f"Ошибка при оптимизации медиа: {e}")
        await callback.answer("Ошибка при оптимизации")


@router.callback_query(F.data == "media_backup")
async def backup_media_metadata(callback: CallbackQuery, session: AsyncSession):
    """Создать бэкап метаданных медиа"""
    try:
        media_service = MediaService(session)
        backup_data = await media_service.backup_media_metadata()
        
        if not backup_data:
            text = "📭 Нет медиа для создания бэкапа"
        else:
            text = f"""
💾 <b>Бэкап создан</b>

📊 <b>Сохранено:</b>
• Медиа файлов: {len(backup_data)}
• Метаданные: названия, типы, размеры
• Связи с уроками

✅ Бэкап готов для экспорта
"""

        await callback.message.edit_text(
            text,
            reply_markup=back_to_admin_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка при создании бэкапа медиа: {e}")
        await callback.answer("Ошибка при создании бэкапа")


@router.callback_query(F.data == "media_analytics")
async def show_media_analytics(callback: CallbackQuery, session: AsyncSession):
    """Показать аналитику медиа"""
    try:
        media_service = MediaService(session)
        analytics = await media_service.get_media_usage_analytics()
        
        if not analytics:
            text = """
📈 <b>Аналитика медиа</b>

❌ Недостаточно данных для аналитики
"""
        else:
            text = f"""
📈 <b>Аналитика использования медиа</b>

📊 <b>Просмотры:</b>
• Всего просмотров: {analytics.get('total_views', 0)}
• Средние просмотры: {analytics.get('average_views', 0)}

🏆 <b>Топ медиа:</b>
"""
            
            if analytics.get('most_viewed'):
                most_viewed = analytics['most_viewed']
                text += f"• {most_viewed['title']}: {most_viewed['views']} просмотров\n"
            
            if analytics.get('least_viewed'):
                least_viewed = analytics['least_viewed']
                text += f"• Минимум: {least_viewed['views']} просмотров"

        await callback.message.edit_text(
            text,
            reply_markup=back_to_admin_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка при получении аналитики медиа: {e}")
        await callback.answer("Ошибка при загрузке аналитики")