"""
Административные обработчики для управления уроками
"""
import logging
from datetime import datetime, timezone
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from services.lesson import LessonService
from services.admin import AdminService
from database.models import Lesson
from keyboards.admin import (
    lessons_list_keyboard,
    lesson_edit_keyboard,
    lesson_type_keyboard,
    confirm_action_keyboard,
    confirm_lesson_delete_keyboard,
    lessons_management_keyboard,
    back_to_admin_keyboard
)
from states.admin import LessonManagementStates
from middlewares.admin import AdminOnlyMiddleware

logger = logging.getLogger(__name__)

# Роутер для управления уроками
router = Router()
router.message.middleware(AdminOnlyMiddleware())
router.callback_query.middleware(AdminOnlyMiddleware())


@router.callback_query(F.data == "admin_lessons_list")
async def show_lessons_list(callback: CallbackQuery, session: AsyncSession):
    """Показать список всех уроков"""
    try:
        lesson_service = LessonService(session)
        
        # Получаем уроки с пагинацией
        lessons, total_lessons = await lesson_service.get_lessons_paginated(
            page=0, 
            per_page=10,
            include_inactive=True  # Показываем все уроки для админа
        )
        
        if not lessons:
            await callback.message.edit_text(
                "📚 <b>Список уроков пуст</b>\n\nНачните с создания первого урока!",
                reply_markup=back_to_admin_keyboard()
            )
            await callback.answer()
            return
        
        lessons_text = f"""
📚 <b>Список всех уроков</b>

📊 <b>Всего уроков:</b> {total_lessons}

📋 <b>Выберите урок для редактирования:</b>
"""
        
        await callback.message.edit_text(
            lessons_text,
            reply_markup=lessons_list_keyboard(lessons, page=0)
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка при показе списка уроков: {e}")
        await callback.answer("❌ Ошибка при загрузке списка уроков.")


@router.callback_query(F.data.startswith("admin_lessons_page:"))
async def navigate_lessons_pages(callback: CallbackQuery, session: AsyncSession):
    """Навигация по страницам уроков"""
    try:
        page = int(callback.data.split(":")[1])
        lesson_service = LessonService(session)
        
        lessons, total_lessons = await lesson_service.get_lessons_paginated(
            page=page, 
            per_page=10,
            include_inactive=True
        )
        
        if not lessons and page > 0:
            # Если страница пустая, показываем первую
            lessons, total_lessons = await lesson_service.get_lessons_paginated(
                page=0, 
                per_page=10,
                include_inactive=True
            )
            page = 0
        
        lessons_text = f"""
📚 <b>Список всех уроков</b>

📊 <b>Всего уроков:</b> {total_lessons}
📄 <b>Страница:</b> {page + 1}

📋 <b>Выберите урок для редактирования:</b>
"""
        
        await callback.message.edit_text(
            lessons_text,
            reply_markup=lessons_list_keyboard(lessons, page=page)
        )
        await callback.answer()
        
    except (ValueError, IndexError):
        await callback.answer("❌ Некорректная страница")
    except Exception as e:
        logger.error(f"Ошибка при навигации по урокам: {e}")
        await callback.answer("❌ Ошибка при загрузке страницы.")


@router.callback_query(F.data.startswith("admin_edit_lesson:"))
async def edit_lesson_menu(callback: CallbackQuery, session: AsyncSession):
    """Меню редактирования конкретного урока"""
    try:
        lesson_id = int(callback.data.split(":")[1])
        
        lesson_service = LessonService(session)
        lesson = await lesson_service.get_lesson_by_id(lesson_id, include_inactive=True)
        
        if not lesson:
            await callback.answer("❌ Урок не найден")
            return
        
        status_text = "✅ Активен" if lesson.is_active else "❌ Неактивен"
        type_text = "🎁 Бесплатный" if lesson.is_free else f"💰 {lesson.price_stars} ⭐"
        
        lesson_text = f"""
📚 <b>Редактирование урока</b>

<b>📖 Название:</b> {lesson.title}

<b>📝 Описание:</b> {lesson.description[:100]}{'...' if len(lesson.description) > 100 else ''}

<b>💰 Стоимость:</b> {type_text}
<b>📁 Категория:</b> {lesson.category or 'Не указана'}
<b>🔄 Статус:</b> {status_text}
<b>👀 Просмотры:</b> {lesson.views_count}

<b>🎬 Тип контента:</b> {lesson.content_type.upper() if lesson.content_type else 'Не указан'}

Выберите параметр для редактирования:
"""
        
        await callback.message.edit_text(
            lesson_text,
            reply_markup=lesson_edit_keyboard(lesson_id)
        )
        await callback.answer()
        
    except (ValueError, IndexError):
        await callback.answer("❌ Некорректный ID урока")
    except Exception as e:
        logger.error(f"Ошибка при загрузке урока для редактирования: {e}")
        await callback.answer("❌ Ошибка при загрузке урока.")


@router.callback_query(F.data == "admin_create_lesson")
async def start_lesson_creation(callback: CallbackQuery, state: FSMContext):
    """Начать создание нового урока"""
    try:
        print(f"\n==== START LESSON CREATION ====")
        print(f"Setting FSM state to creating_lesson")
        
        await state.set_state(LessonManagementStates.creating_lesson)
        await state.update_data(step="title")
        
        # Проверяем, что сохранилось
        current_state = await state.get_state()
        data = await state.get_data()
        print(f"FSM state set to: {current_state}")
        print(f"FSM data: {data}")
        print(f"==============================\n")
        
        create_text = """
➕ <b>Создание нового урока</b>

📝 <b>Шаг 1 из 6:</b> Введите название урока

Отправьте сообщение с названием урока (максимум 200 символов):
"""
        
        await callback.message.edit_text(
            create_text,
            reply_markup=back_to_admin_keyboard()
        )
        await callback.answer("📝 Введите название урока")
        
    except Exception as e:
        logger.error(f"Ошибка при начале создания урока: {e}")
        await callback.answer("❌ Ошибка при создании урока.")


@router.message(LessonManagementStates.creating_lesson, F.content_type == "text")
async def process_lesson_creation(message: Message, state: FSMContext, session: AsyncSession):
    """Обработка создания урока по шагам"""
    print(f"\n==== PROCESS LESSON CREATION ====")
    print(f"Message content_type: {message.content_type}")
    print(f"Message text: {message.text}")
    
    try:
        data = await state.get_data()
        step = data.get("step")
        print(f"Current step: {step}")
        print(f"FSM data: {data}")
        print(f"=================================\n")
        
        if step == "title":
            # Сохраняем название
            if len(message.text) > 200:
                await message.answer("❌ Название слишком длинное. Максимум 200 символов.")
                return
            
            await state.update_data(title=message.text, step="description")
            
            await message.answer("""
📝 <b>Шаг 2 из 6:</b> Введите описание урока

Отправьте подробное описание урока (максимум 1000 символов):
""")
        
        elif step == "description":
            # Сохраняем описание
            if len(message.text) > 1000:
                await message.answer("❌ Описание слишком длинное. Максимум 1000 символов.")
                return
            
            await state.update_data(description=message.text, step="price")
            
            await message.answer("""
💰 <b>Шаг 3 из 6:</b> Укажите стоимость урока

Введите количество звезд Telegram (или 0 для бесплатного урока):
""")
        
        elif step == "price":
            # Сохраняем цену
            try:
                price = int(message.text)
                if price < 0:
                    await message.answer("❌ Цена не может быть отрицательной.")
                    return
                
                await state.update_data(price_stars=price, step="category")
                
                await message.answer("""
📁 <b>Шаг 4 из 6:</b> Укажите категорию урока

Введите название категории (например: "Программирование", "Дизайн", "Маркетинг"):
""")
                
            except ValueError:
                await message.answer("❌ Введите корректное число.")
                return
        
        elif step == "category":
            # Обрабатываем категорию с автоматическим созданием
            from services.category import CategoryService
            
            category_service = CategoryService(session)
            category_name = message.text.strip()
            
            # Находим или создаём категорию
            category, created = await category_service.find_or_create_category(category_name)
            
            if created:
                category_status = f"🆕 <b>Новая категория создана:</b> {category.name}"
            else:
                category_status = f"✅ <b>Категория найдена:</b> {category.name}"
            
            # Сохраняем ID категории и её название
            await state.update_data(
                category_id=category.id, 
                category_name=category.name, 
                step="content_type"
            )
            
            response_text = f"""
{category_status}

🎬 <b>Шаг 5 из 6:</b> Выберите тип контента урока
"""
            
            await message.answer(
                response_text,
                reply_markup=lesson_type_keyboard()
            )
        
    except Exception as e:
        logger.error(f"Ошибка при обработке создания урока: {e}")
        await message.answer("❌ Ошибка при создании урока.")


@router.callback_query(F.data.startswith("lesson_type:"), LessonManagementStates.creating_lesson)
async def select_lesson_type(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Выбор типа контента урока"""
    try:
        content_type = callback.data.split(":")[1]
        print(f"\n==== SELECT LESSON TYPE ====")
        print(f"Selected content_type: {content_type}")
        print(f"Setting step to 'content'")
        
        await state.update_data(content_type=content_type, step="content")
        
        # Проверяем, что сохранилось
        data = await state.get_data()
        print(f"FSM data after update: {data}")
        current_state = await state.get_state()
        print(f"Current FSM state: {current_state}")
        print(f"============================\n")
        
        type_names = {
            "video": "🎥 Видео",
            "photo": "📷 Фото",
            "text": "📝 Текст"
        }
        
        type_name = type_names.get(content_type, content_type)
        
        if content_type == "text":
            # Для текстовых уроков не нужен медиа файл
            await state.update_data(file_id=None)  # Отмечаем, что медиа нет
            await finalize_lesson_creation(callback, state, session)
        else:
            await callback.message.edit_text(f"""
📤 <b>Шаг 6 из 6:</b> Загрузите контент урока

Выбранный тип: {type_name}

Отправьте медиа-файл соответствующего типа:
""")
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка при выборе типа урока: {e}")
        await callback.answer("❌ Ошибка при выборе типа.")


async def finalize_lesson_creation(callback_or_message, state: FSMContext, session: AsyncSession):
    """Завершение создания урока"""
    try:
        data = await state.get_data()
        
        # Создаем урок через сервис
        lesson_service = LessonService(session)
        
        lesson_data = {
            'title': data["title"],
            'description': data["description"],
            'price_stars': data["price_stars"],
            'content_type': data["content_type"],
            'file_id': data.get("file_id"),
            'duration': data.get("duration"),
            'category': data.get("category_name") or "Не указано",
            'category_id': data.get("category_id"),  # Добавляем category_id
            'is_active': True
        }
        
        new_lesson = await lesson_service.create_lesson(lesson_data)
        
        await state.clear()
        
        if not new_lesson:
            error_msg = "❌ Ошибка при создании урока"
            if hasattr(callback_or_message, 'message'):
                await callback_or_message.message.edit_text(error_msg)
            else:
                await callback_or_message.answer(error_msg)
            return
        
        success_text = f"""
✅ <b>Урок успешно создан!</b>

📚 <b>Название:</b> {data["title"]}
💰 <b>Стоимость:</b> {"🎁 Бесплатный" if data["price_stars"] == 0 else f"{data['price_stars']} ⭐"}
📁 <b>Категория:</b> {data.get("category_name", "Не указана")}
🎬 <b>Тип:</b> {data["content_type"]}

Урок активен и доступен пользователям!
"""
        
        # Отправляем сообщение об успехе
        if hasattr(callback_or_message, 'message'):
            # CallbackQuery
            await callback_or_message.message.edit_text(
                success_text,
                reply_markup=back_to_admin_keyboard()
            )
        else:
            # Message
            await callback_or_message.answer(
                success_text,
                reply_markup=back_to_admin_keyboard()
            )
        
    except Exception as e:
        logger.error(f"Ошибка при завершении создания урока: {e}")
        if hasattr(callback_or_message, 'message'):
            await callback_or_message.answer("❌ Ошибка при сохранении урока.")
        else:
            await callback_or_message.answer("❌ Ошибка при сохранении урока.")


@router.message(LessonManagementStates.creating_lesson, F.content_type.in_(["video", "photo"]))
async def process_lesson_media(message: Message, state: FSMContext, session: AsyncSession):
    """Обработка загрузки медиа для урока"""
    print(f"\n\n==== MEDIA HANDLER CALLED ====")
    print(f"message.content_type: {message.content_type}")
    print(f"message.from_user.id: {message.from_user.id if message.from_user else 'None'}")
    print(f"================================\n")
    
    try:
        data = await state.get_data()
        logger.error(f"🚀 MEDIA HANDLER TRIGGERED: content_type={message.content_type}, step={data.get('step')}, expected_content={data.get('content_type')}, user_id={message.from_user.id}")
        print(f"🚀 MEDIA HANDLER TRIGGERED: content_type={message.content_type}, step={data.get('step')}, expected_content={data.get('content_type')}, user_id={message.from_user.id}")
        
        # Проверяем, что мы на правильном шаге
        if data.get("step") != "content":
            logger.error(f"MEDIA UPLOAD: Wrong step. Expected 'content', got '{data.get('step')}'")
            await message.answer(f"❌ Неправильный шаг. Ожидается 'content', получен '{data.get('step')}'")
            return
        
        # Получаем file_id в зависимости от типа контента
        file_id = None
        duration = None
        expected_content_type = data.get("content_type")
        
        logger.error(f"MEDIA UPLOAD: Expected={expected_content_type}, Received={message.content_type}")
        
        if expected_content_type == "video" and message.video:
            file_id = message.video.file_id
            duration = message.video.duration
            logger.error(f"MEDIA UPLOAD: Video processed - file_id={file_id}, duration={duration}")
        elif expected_content_type == "photo" and message.photo:
            file_id = message.photo[-1].file_id  # Берем самое большое фото
            logger.error(f"MEDIA UPLOAD: Photo processed - file_id={file_id}")
        else:
            logger.error(f"MEDIA UPLOAD: Type mismatch - expected={expected_content_type}, received={message.content_type}")
            logger.error(f"MEDIA UPLOAD: message.video exists: {message.video is not None}")
            logger.error(f"MEDIA UPLOAD: message.photo exists: {message.photo is not None}")
        
        if not file_id:
            type_names = {
                "video": "видео",
                "photo": "фото"
            }
            error_msg = f"❌ Отправьте медиа-файл типа {type_names.get(expected_content_type, expected_content_type)}"
            logger.error(f"MEDIA UPLOAD: {error_msg}")
            await message.answer(error_msg)
            return
        
        # Сохраняем данные медиа
        await state.update_data(file_id=file_id, duration=duration)
        logger.error(f"MEDIA UPLOAD: Data saved, calling finalize_lesson_creation")
        
        # Завершаем создание урока
        await finalize_lesson_creation(message, state, session)
        
    except Exception as e:
        logger.error(f"Ошибка при обработке медиа урока: {e}")
        await message.answer("❌ Ошибка при загрузке медиа.")


@router.callback_query(F.data.startswith("edit_lesson_title:"))
async def edit_lesson_title(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Начать редактирование названия урока"""
    try:
        lesson_id = int(callback.data.split(":")[1])
        await state.set_state(LessonManagementStates.editing_lesson_title)
        await state.update_data(editing_lesson_id=lesson_id)
        
        lesson_service = LessonService(session)
        lesson = await lesson_service.get_lesson_by_id(lesson_id, include_inactive=True)
        
        edit_text = f"""
✏️ <b>Редактирование названия урока</b>

📝 <b>Текущее:</b> {lesson.title}

Отправьте новое название (макс 200 симв.):
"""
        
        await callback.message.edit_text(edit_text, reply_markup=back_to_admin_keyboard())
        await callback.answer("✏️ Введите новое название")
    except Exception as e:
        await callback.answer("❌ Ошибка")


@router.callback_query(F.data.startswith("edit_lesson_description:"))
async def edit_lesson_description(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Начать редактирование описания урока"""
    try:
        lesson_id = int(callback.data.split(":")[1])
        await state.set_state(LessonManagementStates.editing_lesson_description)
        await state.update_data(editing_lesson_id=lesson_id)
        
        lesson_service = LessonService(session)
        lesson = await lesson_service.get_lesson_by_id(lesson_id, include_inactive=True)
        
        edit_text = f"""
✏️ <b>Редактирование описания урока</b>

📝 <b>Текущее:</b> {lesson.description if lesson.description else 'Не задано'}

Отправьте новое описание (макс 1000 симв.):
"""
        
        await callback.message.edit_text(edit_text, reply_markup=back_to_admin_keyboard())
        await callback.answer("✏️ Введите новое описание")
    except Exception as e:
        await callback.answer("❌ Ошибка")


@router.message(LessonManagementStates.editing_lesson_title)
async def process_lesson_title_edit(message: Message, session: AsyncSession, state: FSMContext):
    """Обработка нового названия"""
    try:
        if not message.text or len(message.text) > 200:
            await message.answer("❌ Название слишком длинное. Макс 200 симв.")
            return
        
        data = await state.get_data()
        lesson_id = data.get("editing_lesson_id")
        
        if not lesson_id:
            await message.answer("❌ Ошибка: ID урока не найден")
            await state.clear()
            return
        
        lesson_service = LessonService(session)
        lesson = await lesson_service.get_lesson_by_id(lesson_id, include_inactive=True)
        
        if not lesson:
            await message.answer("❌ Урок не найден")
            await state.clear()
            return
        
        # Обновляем название
        lesson.title = message.text
        lesson.updated_at = datetime.now(timezone.utc)
        
        await session.commit()
        
        success_text = f"""
✅ <b>Название урока обновлено</b>

<b>📜 Новое название:</b> {message.text}

Изменения сохранены!
"""
        
        await message.answer(
            success_text,
            reply_markup=back_to_admin_keyboard()
        )
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Ошибка при обновлении названия: {e}")
        await message.answer("❌ Ошибка при обновлении")
        await state.clear()


@router.message(LessonManagementStates.editing_lesson_description)
async def process_lesson_description_edit(message: Message, session: AsyncSession, state: FSMContext):
    """Обработка нового описания"""
    try:
        if not message.text or len(message.text) > 1000:
            await message.answer("❌ Описание слишком длинное. Макс 1000 симв.")
            return
        
        data = await state.get_data()
        lesson_id = data.get("editing_lesson_id")
        
        lesson_service = LessonService(session)
        success = await lesson_service.update_lesson_description(lesson_id, message.text)
        
        if success:
            await message.answer("✅ Описание обновлено")
        else:
            await message.answer("❌ Ошибка обновления")
        
        await state.clear()
        
    except Exception as e:
        await message.answer("❌ Ошибка")


@router.callback_query(F.data.startswith("delete_lesson:"))
async def confirm_lesson_deletion(callback: CallbackQuery, session: AsyncSession):
    """Показать подтверждение удаления урока"""
    try:
        lesson_id = int(callback.data.split(":")[1])
        
        lesson_service = LessonService(session)
        lesson = await lesson_service.get_lesson_by_id(lesson_id, include_inactive=True)
        
        if not lesson:
            await callback.answer("❌ Урок не найден")
            return
        
        confirmation_text = f"""
⚠️ <b>Подтвердите удаление</b>

📚 <b>Урок:</b> {lesson.title}
💰 <b>Цена:</b> {'🎁 Бесплатно' if lesson.is_free else f'⭐ {lesson.price_stars}'}
📈 <b>Просмотров:</b> {lesson.views_count}

❗ <b>Внимание:</b> Это действие нельзя отменить!
Урок будет полностью удалён из базы данных.

Вы уверены, что хотите удалить этот урок?
"""
        
        from keyboards.admin import confirm_lesson_delete_keyboard
        
        await callback.message.edit_text(
            confirmation_text,
            reply_markup=confirm_lesson_delete_keyboard(lesson_id)
        )
        await callback.answer()
        
    except (ValueError, IndexError):
        await callback.answer("❌ Некорректный ID урока")
    except Exception as e:
        logger.error(f"Ошибка при подтверждении удаления: {e}")
        await callback.answer("❌ Ошибка")


@router.callback_query(F.data.startswith("confirm_delete_lesson:"))
async def delete_lesson_confirmed(callback: CallbackQuery, session: AsyncSession):
    """Выполнить удаление урока после подтверждения"""
    try:
        lesson_id = int(callback.data.split(":")[1])
        
        lesson_service = LessonService(session)
        lesson = await lesson_service.get_lesson_by_id(lesson_id, include_inactive=True)
        
        if not lesson:
            await callback.answer("❌ Урок не найден")
            return
        
        lesson_title = lesson.title  # Сохраняем название для сообщения
        
        # Удаляем урок через сервис
        success = await lesson_service.delete_lesson(lesson_id)
        
        if success:
            success_text = f"""
✅ <b>Урок успешно удалён</b>

📚 <b>Удалённый урок:</b> {lesson_title}

✨ Урок полностью удалён из системы.
Все связанные данные также удалены.
"""
            
            from keyboards.admin import lessons_management_keyboard
            
            await callback.message.edit_text(
                success_text,
                reply_markup=lessons_management_keyboard()
            )
            await callback.answer("✅ Урок удалён")
        else:
            await callback.answer("❌ Ошибка при удалении")
        
    except (ValueError, IndexError):
        await callback.answer("❌ Некорректный ID урока")
    except Exception as e:
        logger.error(f"Ошибка при удалении урока: {e}")
        await callback.answer("❌ Ошибка при удалении")


# ВАЖНО: Отладочный обработчик должен быть ПОСЛЕДНИМ в файле!
@router.message(LessonManagementStates.creating_lesson)
async def debug_lesson_creation_messages(message: Message, state: FSMContext):
    """Отладочный обработчик для неопознанных сообщений при создании урока"""
    print(f"\n\n==== DEBUG HANDLER CALLED ====")
    print(f"message.content_type: {message.content_type}")
    print(f"message.from_user.id: {message.from_user.id if message.from_user else 'None'}")
    
    data = await state.get_data()
    print(f"FSM data: {data}")
    print(f"================================\n")
    
    logger.error(f"🚨 UNHANDLED MESSAGE in creating_lesson: content_type={message.content_type}, step={data.get('step')}, expected_content={data.get('content_type')}, user_id={message.from_user.id}")
    print(f"🚨 UNHANDLED MESSAGE in creating_lesson: content_type={message.content_type}, step={data.get('step')}, expected_content={data.get('content_type')}, user_id={message.from_user.id}")
    
    if data.get("step") == "content":
        content_type = data.get("content_type")
        if content_type in ["video", "photo"]:
            await message.answer(f"❌ Неожиданный тип файла: {message.content_type}. Ожидается: {content_type}")
        else:
            await message.answer(f"❌ Отправьте {content_type}-файл для завершения создания урока")
    else:
        await message.answer(f"❌ Неожиданное сообщение на шаге: {data.get('step')}")








@router.callback_query(F.data == "admin_delete_lesson")
async def start_lesson_deletion(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Начать процесс удаления урока"""
    try:
        await state.set_state(LessonManagementStates.deleting_lesson)
        
        lesson_service = LessonService(session)
        lessons, total_count = await lesson_service.get_lessons_paginated(
            page=0, per_page=10, include_inactive=True
        )
        
        if not lessons:
            await callback.message.edit_text(
                "📚 <b>Уроки не найдены</b>\n\nНет уроков для удаления.",
                reply_markup=back_to_admin_keyboard()
            )
            return
        
        delete_text = f"""
🗑️ <b>Удаление урока</b>

📊 <b>Всего уроков:</b> {total_count}

📋 <b>Выберите урок для удаления:</b>
"""
        
        await callback.message.edit_text(
            delete_text,
            reply_markup=lessons_list_keyboard(lessons, page=0)
        )
        await callback.answer("🗑️ Выберите урок")
        
    except Exception as e:
        logger.error(f"Ошибка при начале удаления: {e}")
        await callback.answer("❌ Ошибка")


@router.callback_query(F.data.startswith("admin_confirm_delete:"))
async def confirm_lesson_deletion(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Подтверждение удаления урока"""
    try:
        lesson_id = int(callback.data.split(":")[1])
        
        lesson_service = LessonService(session)
        lesson = await lesson_service.get_lesson_by_id(lesson_id, include_inactive=True)
        
        if not lesson:
            await callback.answer("❌ Урок не найден")
            return
        
        can_delete, reason = await lesson_service.can_delete_lesson(lesson_id)
        dependencies = await lesson_service.get_lesson_dependencies(lesson_id)
        
        await state.set_state(LessonManagementStates.confirming_lesson_deletion)
        await state.update_data(deleting_lesson_id=lesson_id)
        
        status_text = "✅ Активен" if lesson.is_active else "❌ Неактивен"
        type_text = "🎁 Бесплатный" if lesson.is_free else f"💰 {lesson.price_stars} ⭐"
        
        confirm_text = f"""
🗑️ <b>Подтверждение удаления урока</b>

<b>📖 Название:</b> {lesson.title}

<b>💰 Стоимость:</b> {type_text}
<b>🔄 Статус:</b> {status_text}

<b>📈 Статистика:</b>
• Просмотры: {dependencies.get('views_count', 0)}
• Покупки: {dependencies.get('total_purchases', 0)}
• Доход: {dependencies.get('total_revenue', 0)} ⭐

⚠️ <b>Вы уверены, что хотите удалить этот урок?</b>
"""
        
        from keyboards.admin import simple_confirmation_keyboard
        
        # Простое подтверждение - без выбора типа удаления
        confirm_keyboard = simple_confirmation_keyboard(
            action_data=f"confirm_delete_lesson:{lesson_id}",
            cancel_data="admin_lessons_list"
        )
        
        await callback.message.edit_text(
            confirm_text,
            reply_markup=confirm_keyboard
        )
        await callback.answer()
        
    except (ValueError, IndexError):
        await callback.answer("❌ Некорректный ID урока")
    except Exception as e:
        logger.error(f"Ошибка при подтверждении удаления: {e}")
        await callback.answer("❌ Ошибка")


@router.callback_query(F.data.startswith("confirm_delete_lesson:"))
async def execute_lesson_deletion(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Выполнить удаление урока"""
    try:
        lesson_id = int(callback.data.split(":")[1])
        
        lesson_service = LessonService(session)
        lesson = await lesson_service.get_lesson_by_id(lesson_id, include_inactive=True)
        
        if not lesson:
            await callback.answer("❌ Урок не найден")
            return
        
        lesson_title = lesson.title
        
        # Проверяем, можно ли безопасно удалить
        can_delete, reason = await lesson_service.can_delete_lesson(lesson_id)
        
        if can_delete:
            # Безопасное удаление (жесткое)
            success = await lesson_service.delete_lesson(lesson_id, force=False)
            delete_type = "полностью удален"
        else:
            # Мягкое удаление (деактивация)
            success = await lesson_service.soft_delete_lesson(lesson_id)
            delete_type = "деактивирован"
        
        if success:
            success_text = f"""
✅ <b>Урок успешно удален</b>

<b>📖 Урок:</b> {lesson_title}

Урок {delete_type} и больше не доступен пользователям.
"""
            
            await callback.message.edit_text(
                success_text,
                reply_markup=back_to_admin_keyboard()
            )
            await callback.answer(f"✅ Урок {delete_type}")
        else:
            await callback.answer("❌ Ошибка при удалении")
        
        await state.clear()
        
    except (ValueError, IndexError):
        await callback.answer("❌ Некорректный ID урока")
    except Exception as e:
        logger.error(f"Ошибка при удалении урока: {e}")
        await callback.answer("❌ Ошибка")


@router.callback_query(F.data.startswith("soft_delete:"))
async def execute_soft_delete(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Выполнить мягкое удаление (деактивация)"""
    try:
        lesson_id = int(callback.data.split(":")[1])
        
        lesson_service = LessonService(session)
        lesson = await lesson_service.get_lesson_by_id(lesson_id, include_inactive=True)
        
        if not lesson:
            await callback.answer("❌ Урок не найден")
            return
        
        success = await lesson_service.soft_delete_lesson(lesson_id)
        
        if success:
            success_text = f"""
✅ <b>Мягкое удаление выполнено</b>

<b>📖 Урок:</b> {lesson.title}

Урок деактивирован и больше не доступен пользователям.
Данные сохранены для статистики.
"""
            
            await callback.message.edit_text(
                success_text,
                reply_markup=back_to_admin_keyboard()
            )
            await callback.answer("✅ Урок деактивирован")
        else:
            await callback.answer("❌ Ошибка при деактивации")
        
        await state.clear()
        
    except (ValueError, IndexError):
        await callback.answer("❌ Некорректный ID урока")
    except Exception as e:
        logger.error(f"Ошибка при мягком удалении: {e}")
        await callback.answer("❌ Ошибка")


@router.callback_query(F.data.startswith("hard_delete:"))
async def execute_hard_delete(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Выполнить жесткое удаление"""
    try:
        lesson_id = int(callback.data.split(":")[1])
        
        lesson_service = LessonService(session)
        lesson = await lesson_service.get_lesson_by_id(lesson_id, include_inactive=True)
        
        if not lesson:
            await callback.answer("❌ Урок не найден")
            return
        
        lesson_title = lesson.title
        success = await lesson_service.delete_lesson(lesson_id, force=False)
        
        if success:
            success_text = f"""
✅ <b>Жесткое удаление выполнено</b>

<b>📖 Урок:</b> {lesson_title}

Урок полностью удален из базы данных.

⚠️ <b>Внимание:</b> Это действие необратимо!
"""
            
            await callback.message.edit_text(
                success_text,
                reply_markup=back_to_admin_keyboard()
            )
            await callback.answer("✅ Урок полностью удален")
        else:
            await callback.answer("❌ Ошибка при удалении")
        
        await state.clear()
        
    except (ValueError, IndexError):
        await callback.answer("❌ Некорректный ID урока")
    except Exception as e:
        logger.error(f"Ошибка при жестком удалении: {e}")
        await callback.answer("❌ Ошибка")


@router.callback_query(F.data.startswith("force_delete:"))
async def execute_force_delete(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Выполнить принудительное удаление"""
    try:
        lesson_id = int(callback.data.split(":")[1])
        
        lesson_service = LessonService(session)
        lesson = await lesson_service.get_lesson_by_id(lesson_id, include_inactive=True)
        
        if not lesson:
            await callback.answer("❌ Урок не найден")
            return
        
        lesson_title = lesson.title
        success = await lesson_service.delete_lesson(lesson_id, force=True)
        
        if success:
            success_text = f"""
⚠️ <b>Принудительное удаление выполнено</b>

<b>📖 Урок:</b> {lesson_title}

Урок и все связанные данные полностью удалены.
Покупки отменены.

⚠️ <b>Внимание:</b> Это действие необратимо!
"""
            
            await callback.message.edit_text(
                success_text,
                reply_markup=back_to_admin_keyboard()
            )
            await callback.answer("⚠️ Принудительно удален")
        else:
            await callback.answer("❌ Ошибка при удалении")
        
        await state.clear()
        
    except (ValueError, IndexError):
        await callback.answer("❌ Некорректный ID урока")
    except Exception as e:
        logger.error(f"Ошибка при принудительном удалении: {e}")
        await callback.answer("❌ Ошибка")


@router.callback_query(F.data.startswith("edit_lesson_price:"))
async def edit_lesson_price(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Начать редактирование цены урока"""
    try:
        lesson_id = int(callback.data.split(":")[1])
        await state.set_state(LessonManagementStates.editing_lesson_price)
        await state.update_data(editing_lesson_id=lesson_id)
        
        lesson_service = LessonService(session)
        lesson = await lesson_service.get_lesson_by_id(lesson_id, include_inactive=True)
        
        edit_text = f"""
💰 <b>Редактирование цены урока</b>

💰 <b>Текущая цена:</b> ⭐ {lesson.price_stars}
🎁 <b>Бесплатный:</b> {'Да' if lesson.is_free else 'Нет'}

Отправьте новую цену в Telegram Stars (число от 1 до 2500):
Или отправьте 0 для бесплатного урока.
"""
        
        await callback.message.edit_text(edit_text, reply_markup=back_to_admin_keyboard())
        await callback.answer("💰 Введите новую цену")
    except Exception as e:
        await callback.answer("❌ Ошибка")


@router.callback_query(F.data.startswith("edit_lesson_media:"))
async def edit_lesson_media(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Начать редактирование медиа-материала урока"""
    try:
        lesson_id = int(callback.data.split(":")[1])
        
        lesson_service = LessonService(session)
        lesson = await lesson_service.get_lesson_by_id(lesson_id, include_inactive=True)
        
        if not lesson:
            await callback.answer("❌ Урок не найден")
            return
        
        # Определяем текущий тип медиа и наличие
        has_media = lesson.file_id is not None
        media_info = ""
        
        if has_media:
            if lesson.content_type == "video":
                media_info = f"🎥 Текущий материал: Видео"
            elif lesson.content_type == "photo":
                media_info = f"📷 Текущий материал: Фото"
            else:
                media_info = f"📝 Текущий материал: Текст"
        else:
            media_info = "❌ Материал отсутствует"
        
        edit_text = f"""
🎬 <b>Редактирование медиа-материала</b>

📚 <b>Урок:</b> {lesson.title}

{media_info}

Выберите тип медиа для {'<b>обновления</b>' if has_media else '<b>загрузки</b>'}:
"""
        
        from keyboards.admin import media_update_type_keyboard
        
        await callback.message.edit_text(
            edit_text,
            reply_markup=media_update_type_keyboard(lesson_id)
        )
        await callback.answer()
        
    except (ValueError, IndexError):
        await callback.answer("❌ Некорректный ID урока")
    except Exception as e:
        logger.error(f"Ошибка при редактировании медиа: {e}")
        await callback.answer("❌ Ошибка")


@router.callback_query(F.data.startswith("update_media_"))
async def start_media_update(callback: CallbackQuery, state: FSMContext):
    """Начать обновление медиа-материала"""
    try:
        data_parts = callback.data.split("_")
        media_type = data_parts[2].split(":")[0]  # video или photo
        lesson_id = int(data_parts[2].split(":")[1])
        
        await state.set_state(LessonManagementStates.editing_lesson_media)
        await state.update_data(
            editing_lesson_id=lesson_id,
            new_media_type=media_type
        )
        
        media_names = {
            "video": "🎥 видео",
            "photo": "📷 фото"
        }
        
        media_name = media_names.get(media_type, media_type)
        
        edit_text = f"""
📤 <b>Загрузка {media_name}</b>

Отправьте {media_name}-файл для обновления урока:
"""
        
        await callback.message.edit_text(
            edit_text,
            reply_markup=back_to_admin_keyboard()
        )
        await callback.answer(f"📤 Отправьте {media_name}")
        
    except (ValueError, IndexError):
        await callback.answer("❌ Некорректные данные")
    except Exception as e:
        logger.error(f"Ошибка при начале обновления медиа: {e}")
        await callback.answer("❌ Ошибка")


@router.message(LessonManagementStates.editing_lesson_media, F.content_type.in_(["video", "photo"]))
async def process_media_update(message: Message, session: AsyncSession, state: FSMContext):
    """Обработка обновления медиа-материала"""
    try:
        data = await state.get_data()
        lesson_id = data.get("editing_lesson_id")
        expected_type = data.get("new_media_type")
        
        if not lesson_id or not expected_type:
            await message.answer("❌ Ошибка: не найдены данные редактирования")
            await state.clear()
            return
        
        # Получаем file_id в зависимости от типа
        file_id = None
        duration = None
        
        if expected_type == "video" and message.video:
            file_id = message.video.file_id
            duration = message.video.duration
        elif expected_type == "photo" and message.photo:
            file_id = message.photo[-1].file_id  # Берем самое большое фото
        
        if not file_id:
            type_names = {
                "video": "видео",
                "photo": "фото"
            }
            await message.answer(f"❌ Отправьте {type_names.get(expected_type, expected_type)}-файл")
            return
        
        # Обновляем урок в базе данных
        lesson_service = LessonService(session)
        lesson = await lesson_service.get_lesson_by_id(lesson_id, include_inactive=True)
        
        if not lesson:
            await message.answer("❌ Урок не найден")
            await state.clear()
            return
        
        # Обновляем поля урока
        lesson.file_id = file_id
        lesson.content_type = expected_type
        lesson.updated_at = datetime.now(timezone.utc)
        
        if duration and expected_type == "video":
            lesson.duration = duration
        
        await session.commit()
        
        action_text = "обновлен" if lesson.file_id else "добавлен"
        type_names = {
            "video": "Видео",
            "photo": "Фото"
        }
        
        success_text = f"""
✅ <b>Медиа-материал успешно {action_text}</b>

📚 <b>Урок:</b> {lesson.title}
🎬 <b>Новый материал:</b> {type_names.get(expected_type, expected_type)}

Изменения сохранены!
"""
        
        await message.answer(
            success_text,
            reply_markup=back_to_admin_keyboard()
        )
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Ошибка при обновлении медиа: {e}")
        await message.answer("❌ Ошибка при обновлении медиа")
        await state.clear()


@router.message(LessonManagementStates.editing_lesson_price)
async def process_lesson_price_edit(message: Message, session: AsyncSession, state: FSMContext):
    """Обработка новой цены"""
    try:
        if not message.text or not message.text.isdigit():
            await message.answer("❌ Введите корректное число от 0 до 2500")
            return
        
        price = int(message.text)
        if price < 0 or price > 2500:
            await message.answer("❌ Цена должна быть от 0 до 2500 ⭐")
            return
        
        data = await state.get_data()
        lesson_id = data.get("editing_lesson_id")
        
        lesson_service = LessonService(session)
        
        # Обновляем цену и статус бесплатности
        success_price = await lesson_service.update_lesson_price(lesson_id, price)
        
        if success_price:
            if price == 0:
                await message.answer("✅ Урок стал бесплатным")
            else:
                await message.answer(f"✅ Цена обновлена: ⭐ {price}")
        else:
            await message.answer("❌ Ошибка обновления")
        
        await state.clear()
        
    except Exception as e:
        await message.answer("❌ Ошибка")