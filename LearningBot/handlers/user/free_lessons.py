"""
Обработчики для бесплатных уроков (лид-магниты)
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from services.lesson import LessonService
from services.user import UserService
from keyboards.user import lesson_detail_keyboard, main_menu_keyboard
from states.user import UserStates

logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(F.data == "free_lesson")
async def show_free_lessons(callback: CallbackQuery, session: AsyncSession):
    """Показать бесплатные уроки"""
    try:
        lesson_service = LessonService(session)
        user_service = UserService(session)
        
        # Логирование активности
        await user_service.log_user_activity(callback.from_user.id, "view_free_lessons")
        
        # Получение бесплатных уроков
        free_lessons = await lesson_service.get_free_lessons()
        
        if not free_lessons:
            # Если нет бесплатных уроков, создаем стандартное приветствие
            await show_default_free_lesson(callback, session)
            return
        
        if len(free_lessons) == 1:
            # Если только один бесплатный урок, показываем его сразу
            lesson = free_lessons[0]
            await show_lesson_detail(callback, lesson, session, is_free=True)
        else:
            # Если несколько уроков, показываем список
            await show_free_lessons_list(callback, free_lessons, session)
            
    except Exception as e:
        logger.error(f"Ошибка при показе бесплатных уроков: {e}")
        await callback.answer("Произошла ошибка при загрузке бесплатных уроков")


async def show_default_free_lesson(callback: CallbackQuery, session: AsyncSession):
    """Показать стандартный бесплатный урок-приветствие"""
    free_lesson_text = """
🎁 <b>Добро пожаловать! Ваш бесплатный AI-урок</b>

📚 <b>Название:</b> Введение в мир искусственного интеллекта
⏱️ <b>Длительность:</b> 5 минут
🎯 <b>Уровень:</b> Для начинающих

📝 <b>В этом уроке вы узнаете:</b>
✅ Что такое ИИ и как он работает
✅ Основные типы машинного обучения
✅ Как выбрать первый AI-проект для старта
✅ Перспективы карьеры в сфере ИИ

<i>Этот урок абсолютно бесплатен и доступен всем пользователям!</i>
"""
    
    # Создаем клавиатуру для бесплатного урока
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶️ Начать урок", callback_data="start_free_lesson:0")],
        [InlineKeyboardButton(text="📚 К каталогу", callback_data="catalog")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])
    
    await callback.message.edit_text(
        free_lesson_text,
        reply_markup=keyboard
    )
    await callback.answer()


async def show_free_lessons_list(callback: CallbackQuery, lessons: list, session: AsyncSession):
    """Показать список бесплатных уроков"""
    lessons_text = "🎁 <b>Бесплатные уроки</b>\n\nВыберите урок для изучения:\n\n"
    
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    
    for lesson in lessons:
        duration_text = f" ({lesson.duration // 60} мин)" if lesson.duration else ""
        lessons_text += f"📚 <b>{lesson.title}</b>{duration_text}\n"
        lessons_text += f"└ {lesson.description[:100]}...\n\n"
        
        builder.row(InlineKeyboardButton(
            text=f"▶️ {lesson.title}",
            callback_data=f"free_lesson:{lesson.id}"
        ))
    
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    
    await callback.message.edit_text(
        lessons_text,
        reply_markup=builder.as_markup()
    )
    await callback.answer()


async def show_lesson_detail(callback: CallbackQuery, lesson, session: AsyncSession, is_free: bool = False):
    """Показать детали урока"""
    duration_text = ""
    if lesson.duration:
        minutes = lesson.duration // 60
        seconds = lesson.duration % 60
        if minutes > 0:
            duration_text = f"⏱️ <b>Длительность:</b> {minutes} мин"
            if seconds > 0:
                duration_text += f" {seconds} сек"
        else:
            duration_text = f"⏱️ <b>Длительность:</b> {seconds} сек"
    
    lesson_text = f"""
🎁 <b>{lesson.title}</b>

{lesson.description}

{duration_text}
🏷️ <b>Категория:</b> {lesson.category or 'Общая'}
👁️ <b>Просмотров:</b> {lesson.views_count}

<i>{'🎁 Этот урок абсолютно бесплатный!' if is_free else f'💰 Цена: {lesson.price_stars} ⭐'}</i>
"""
    
    await callback.message.edit_text(
        lesson_text,
        reply_markup=lesson_detail_keyboard(
            lesson_id=lesson.id, 
            is_free=is_free
        )
    )
    await callback.answer()


@router.callback_query(F.data.startswith("free_lesson:"))
async def show_specific_free_lesson(callback: CallbackQuery, session: AsyncSession):
    """Показать конкретный бесплатный урок"""
    try:
        lesson_id = int(callback.data.split(":")[1])
        
        lesson_service = LessonService(session)
        user_service = UserService(session)
        
        # Получение урока
        lesson = await lesson_service.get_lesson_by_id(lesson_id)
        
        if not lesson:
            await callback.answer("Урок не найден")
            return
        
        if not lesson.is_free:
            await callback.answer("Этот урок не является бесплатным")
            return
        
        # Логирование активности
        await user_service.log_user_activity(
            callback.from_user.id, 
            "view_free_lesson", 
            lesson_id=lesson_id
        )
        
        await show_lesson_detail(callback, lesson, session, is_free=True)
        
    except (ValueError, IndexError):
        await callback.answer("Некорректный ID урока")
    except Exception as e:
        logger.error(f"Ошибка при показе бесплатного урока: {e}")
        await callback.answer("Произошла ошибка")


@router.callback_query(F.data.startswith("get_free:"))
async def get_free_lesson(callback: CallbackQuery, session: AsyncSession):
    """Получить бесплатный урок"""
    try:
        lesson_id = int(callback.data.split(":")[1])
        
        lesson_service = LessonService(session)
        user_service = UserService(session)
        
        # Получение урока
        lesson = await lesson_service.get_lesson_by_id(lesson_id)
        
        if not lesson:
            await callback.answer("Урок не найден")
            return
        
        if not lesson.is_free:
            await callback.answer("Этот урок не является бесплатным")
            return
        
        # Увеличение счетчика просмотров
        await lesson_service.increment_lesson_views(lesson_id)
        
        # Логирование активности
        await user_service.log_user_activity(
            callback.from_user.id, 
            "get_free_lesson", 
            lesson_id=lesson_id
        )
        
        # Показ контента урока
        await show_lesson_content(callback, lesson, session)
        
    except (ValueError, IndexError):
        await callback.answer("Некорректный ID урока")
    except Exception as e:
        logger.error(f"Ошибка при получении бесплатного урока: {e}")
        await callback.answer("Произошла ошибка")


@router.callback_query(F.data.startswith("start_free_lesson:"))
async def start_default_free_lesson(callback: CallbackQuery, session: AsyncSession):
    """Запустить стандартный бесплатный урок"""
    try:
        user_service = UserService(session)
        
        # Логирование активности
        await user_service.log_user_activity(
            callback.from_user.id, 
            "start_default_free_lesson"
        )
        
        # Контент стандартного бесплатного урока
        lesson_content = """
▶️ <b>Урок: Как эффективно учиться с нашим ботом</b>

🎯 <b>Шаг 1: Навигация</b>
• Используйте кнопки меню для быстрого перемещения
• Главное меню всегда доступно через 🏠
• Кнопка "Назад" поможет вернуться на предыдущий экран

💰 <b>Шаг 2: Покупка уроков</b>
• Все платежи проходят через безопасную систему Telegram Stars ⭐
• Оплата мгновенная, доступ к уроку открывается сразу
• Средства списываются автоматически при подтверждении

👤 <b>Шаг 3: Отслеживание прогресса</b>
• В разделе "Мои покупки" видны все ваши уроки
• Статистика трат доступна в настройках профиля
• История активности сохраняется автоматически

🚀 <b>Секрет успеха:</b>
Регулярно возвращайтесь к пройденным урокам для закрепления знаний!

✅ <b>Поздравляем! Вы прошли ваш первый урок!</b>
"""
        
        completion_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📚 Открыть каталог", callback_data="catalog")],
            [InlineKeyboardButton(text="🏆 Мои достижения", callback_data="achievements")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
        ])
        
        await callback.message.edit_text(
            lesson_content,
            reply_markup=completion_keyboard
        )
        
        # Показать поздравление
        await callback.answer("🎉 Поздравляем с завершением первого урока!", show_alert=True)
        
    except Exception as e:
        logger.error(f"Ошибка при запуске стандартного бесплатного урока: {e}")
        await callback.answer("Произошла ошибка")


async def show_lesson_content(callback: CallbackQuery, lesson, session: AsyncSession):
    """Показать контент урока"""
    try:
        content_text = f"""
▶️ <b>{lesson.title}</b>

{lesson.description}

📖 <b>Содержание урока:</b>
"""
        
        # В реальном проекте здесь будет отправка медиа-файла
        if lesson.content_type == "video":
            if lesson.file_id:
                # Отправка видео
                await callback.message.answer_video(
                    video=lesson.file_id,
                    caption=content_text
                )
            else:
                content_text += "\n🎥 Видеоурок будет добавлен в ближайшее время"
                
        elif lesson.content_type == "photo":
            if lesson.file_id:
                # Отправка фото
                await callback.message.answer_photo(
                    photo=lesson.file_id,
                    caption=content_text
                )
            else:
                content_text += "\n📸 Изображения будут добавлены в ближайшее время"
                
        elif lesson.content_type == "document":
            if lesson.file_id:
                # Отправка документа
                await callback.message.answer_document(
                    document=lesson.file_id,
                    caption=content_text
                )
            else:
                content_text += "\n📄 Документ будет добавлен в ближайшее время"
        else:
            content_text += f"\n📝 Текстовый материал урока\n\n{lesson.description}"
        
        # Отправка текстового контента, если не было медиа
        if not lesson.file_id:
            completion_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Урок завершен", callback_data="lesson_completed")],
                [InlineKeyboardButton(text="📚 К каталогу", callback_data="catalog")],
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
            ])
            
            await callback.message.edit_text(
                content_text,
                reply_markup=completion_keyboard
            )
        
        await callback.answer("🎉 Урок успешно получен!")
        
    except Exception as e:
        logger.error(f"Ошибка при показе контента урока: {e}")
        await callback.answer("Произошла ошибка при загрузке урока")


@router.callback_query(F.data == "lesson_completed")
async def lesson_completed(callback: CallbackQuery, session: AsyncSession):
    """Обработчик завершения урока"""
    try:
        user_service = UserService(session)
        
        await user_service.log_user_activity(
            callback.from_user.id, 
            "lesson_completed"
        )
        
        completion_text = """
🎉 <b>Поздравляем с завершением урока!</b>

✅ Урок успешно пройден
🏆 Продолжайте обучение для достижения новых результатов

<i>Что дальше?</i>
"""
        
        next_steps_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📚 Больше уроков", callback_data="catalog")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
        ])
        
        await callback.message.edit_text(
            completion_text,
            reply_markup=next_steps_keyboard
        )
        
        await callback.answer("✅ Урок завершен!")
        
    except Exception as e:
        logger.error(f"Ошибка при завершении урока: {e}")
        await callback.answer("Произошла ошибка")