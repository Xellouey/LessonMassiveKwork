"""
Обработчики для детальной карточки урока
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from services.lesson import LessonService
from services.user import UserService
from keyboards.user import lesson_detail_keyboard, payment_keyboard, main_menu_keyboard, InlineKeyboardButton, InlineKeyboardBuilder
from states.user import UserStates

logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(F.data.startswith("lesson:"))
async def show_lesson_detail(callback: CallbackQuery, session: AsyncSession):
    """Показать детальную информацию об уроке"""
    try:
        lesson_id = int(callback.data.split(":")[1])
        
        lesson_service = LessonService(session)
        user_service = UserService(session)
        
        # Получение урока
        lesson = await lesson_service.get_lesson_by_id(lesson_id)
        
        if not lesson:
            await callback.answer("❌ Урок не найден")
            return
        
        # Проверка, есть ли у пользователя доступ к уроку
        has_access = await lesson_service.check_user_has_lesson(
            callback.from_user.id, 
            lesson_id
        )
        
        # Логирование просмотра
        await user_service.log_user_activity(
            callback.from_user.id, 
            "view_lesson_detail", 
            lesson_id=lesson_id
        )
        
        # Формирование информации об уроке
        content_icon = {
            'video': '🎥 Видеоурок',
            'audio': '🎵 Аудиоурок', 
            'document': '📄 Текстовый урок',
            'photo': '📸 Урок с изображениями'
        }.get(lesson.content_type, '📚 Урок')
        
        # Длительность
        duration_text = ""
        if lesson.duration:
            minutes = lesson.duration // 60
            seconds = lesson.duration % 60
            if minutes > 0:
                duration_text = f"\n⏱️ <b>Длительность:</b> {minutes} мин"
                if seconds > 0:
                    duration_text += f" {seconds} сек"
            else:
                duration_text = f"\n⏱️ <b>Длительность:</b> {seconds} сек"
        
        # Цена
        if lesson.is_free:
            price_text = "\n💰 <b>Цена:</b> 🎁 Бесплатно"
        else:
            from services.currency import CurrencyService
            usd_price = CurrencyService.format_usd_price(lesson.price_usd)
            price_text = f"\n💰 <b>Цена:</b> {usd_price}"
        
        # Статус доступа
        if has_access:
            access_text = "\n✅ <b>Статус:</b> У вас есть доступ к этому уроку"
        else:
            access_text = "\n🔒 <b>Статус:</b> Требуется покупка"
        
        lesson_detail_text = f"""
📚 <b>{lesson.title}</b>

{content_icon}

📝 <b>Описание:</b>
{lesson.description}
{duration_text}
{price_text}
{access_text}

🏷️ <b>Категория:</b> {lesson.category or 'Общая'}
👁️ <b>Просмотров:</b> {lesson.views_count}
📅 <b>Добавлен:</b> {lesson.created_at.strftime('%d.%m.%Y')}
"""
        
        await callback.message.edit_text(
            lesson_detail_text,
            reply_markup=lesson_detail_keyboard(
                lesson_id=lesson_id, 
                is_purchased=has_access, 
                is_free=lesson.is_free
            )
        )
        await callback.answer()
        
    except (ValueError, IndexError):
        await callback.answer("❌ Некорректный ID урока")
    except Exception as e:
        logger.error(f"Ошибка при показе деталей урока: {e}")
        await callback.answer("❌ Произошла ошибка при загрузке урока")


@router.callback_query(F.data.startswith("preview:"))
async def show_lesson_preview(callback: CallbackQuery, session: AsyncSession):
    """Показать превью урока"""
    try:
        lesson_id = int(callback.data.split(":")[1])
        
        lesson_service = LessonService(session)
        user_service = UserService(session)
        
        # Получение урока
        lesson = await lesson_service.get_lesson_by_id(lesson_id)
        
        if not lesson:
            await callback.answer("❌ Урок не найден")
            return
        
        # Логирование просмотра превью
        await user_service.log_user_activity(
            callback.from_user.id, 
            "view_lesson_preview", 
            lesson_id=lesson_id
        )
        
        # Превью контента (первые 200 символов описания)
        preview_description = lesson.description[:200] + "..." if len(lesson.description) > 200 else lesson.description
        
        preview_text = f"""
👀 <b>Превью: {lesson.title}</b>

📝 <b>Краткое содержание:</b>
{preview_description}

<i>🔒 Полный контент доступен после покупки урока</i>

💡 <b>Что вы получите:</b>
• Полный доступ к материалам урока
• Возможность пересмотра в любое время
• Поддержка различных форматов контента
• Отслеживание прогресса обучения
"""
        
        from keyboards.user import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        
        if lesson.is_free:
            builder.row(InlineKeyboardButton(
                text="🎁 Получить бесплатно", 
                callback_data=f"get_free:{lesson_id}"
            ))
        else:
            from services.currency import CurrencyService
            usd_price = CurrencyService.format_usd_price(lesson.price_usd)
            builder.row(InlineKeyboardButton(
                text=f"💳 Купить за {usd_price}", 
                callback_data=f"buy_lesson:{lesson_id}"
            ))
        
        builder.row(
            InlineKeyboardButton(text="🔙 К уроку", callback_data=f"lesson:{lesson_id}"),
            InlineKeyboardButton(text="📚 К каталогу", callback_data="catalog")
        )
        
        await callback.message.edit_text(
            preview_text,
            reply_markup=builder.as_markup()
        )
        await callback.answer("👀 Показано превью урока")
        
    except (ValueError, IndexError):
        await callback.answer("❌ Некорректный ID урока")
    except Exception as e:
        logger.error(f"Ошибка при показе превью урока: {e}")
        await callback.answer("❌ Произошла ошибка")


@router.callback_query(F.data.startswith("info:"))
async def show_lesson_info(callback: CallbackQuery, session: AsyncSession):
    """Показать подробную информацию об уроке"""
    try:
        lesson_id = int(callback.data.split(":")[1])
        
        lesson_service = LessonService(session)
        user_service = UserService(session)
        
        # Получение урока
        lesson = await lesson_service.get_lesson_by_id(lesson_id)
        
        if not lesson:
            await callback.answer("❌ Урок не найден")
            return
        
        # Логирование
        await user_service.log_user_activity(
            callback.from_user.id, 
            "view_lesson_info", 
            lesson_id=lesson_id
        )
        
        # Техническая информация
        content_types = {
            'video': 'Видеоматериал',
            'audio': 'Аудиозапись',
            'document': 'Текстовый документ',
            'photo': 'Изображения и графика'
        }
        
        info_text = f"""
ℹ️ <b>Подробная информация</b>

📚 <b>Название:</b> {lesson.title}

📋 <b>Полное описание:</b>
{lesson.description}

🔧 <b>Технические детали:</b>
• Тип контента: {content_types.get(lesson.content_type, 'Смешанный')}
• ID урока: #{lesson_id}
• Дата создания: {lesson.created_at.strftime('%d.%m.%Y %H:%M')}
• Последнее обновление: {lesson.updated_at.strftime('%d.%m.%Y %H:%M')}

📊 <b>Статистика:</b>
• Просмотров: {lesson.views_count}
• Категория: {lesson.category or 'Без категории'}
• Статус: {'🟢 Активный' if lesson.is_active else '🔴 Неактивный'}

💡 <b>Подходит для:</b>
• Начинающих и продвинутых пользователей
• Самостоятельного изучения
• Практического применения знаний
"""
        
        from keyboards.user import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        
        builder.row(InlineKeyboardButton(
            text="🔙 К уроку", 
            callback_data=f"lesson:{lesson_id}"
        ))
        
        builder.row(
            InlineKeyboardButton(text="📚 К каталогу", callback_data="catalog"),
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
        )
        
        await callback.message.edit_text(
            info_text,
            reply_markup=builder.as_markup()
        )
        await callback.answer()
        
    except (ValueError, IndexError):
        await callback.answer("❌ Некорректный ID урока")
    except Exception as e:
        logger.error(f"Ошибка при показе информации об уроке: {e}")
        await callback.answer("❌ Произошла ошибка")


@router.callback_query(F.data.startswith("buy_lesson:"))
async def initiate_lesson_purchase(callback: CallbackQuery, session: AsyncSession):
    """Инициировать покупку урока"""
    try:
        lesson_id = int(callback.data.split(":")[1])
        
        lesson_service = LessonService(session)
        user_service = UserService(session)
        
        # Получение урока
        lesson = await lesson_service.get_lesson_by_id(lesson_id)
        
        if not lesson:
            await callback.answer("❌ Урок не найден")
            return
        
        if lesson.is_free:
            await callback.answer("❌ Этот урок бесплатный, используйте соответствующую кнопку")
            return
        
        # Проверка, не купил ли пользователь уже этот урок
        has_access = await lesson_service.check_user_has_lesson(
            callback.from_user.id, 
            lesson_id
        )
        
        if has_access:
            await callback.answer("✅ У вас уже есть доступ к этому уроку")
            return
        
        # Логирование намерения покупки
        await user_service.log_user_activity(
            callback.from_user.id, 
            "initiate_purchase", 
            lesson_id=lesson_id
        )
        
        # Показ информации о покупке
        purchase_text = f"""
💳 <b>Покупка урока</b>

📚 <b>Урок:</b> {lesson.title}
💰 <b>Цена:</b> ⭐ {lesson.price_stars} звезд

📝 <b>Что входит в покупку:</b>
• Полный доступ к материалам урока
• Возможность просмотра в любое время
• Пожизненный доступ к контенту
• Поддержка в комментариях

💡 <b>Оплата через Telegram Stars:</b>
• Безопасная система оплаты
• Мгновенное получение доступа
• Автоматическое списание средств

<b>Продолжить покупку?</b>
"""
        
        await callback.message.edit_text(
            purchase_text,
            reply_markup=payment_keyboard(lesson_id, lesson.price_stars)
        )
        await callback.answer()
        
    except (ValueError, IndexError):
        await callback.answer("❌ Некорректный ID урока")
    except Exception as e:
        logger.error(f"Ошибка при инициации покупки: {e}")
        await callback.answer("❌ Произошла ошибка при подготовке к покупке")


@router.callback_query(F.data.startswith("open_lesson:"))
async def open_purchased_lesson(callback: CallbackQuery, session: AsyncSession):
    """Открыть купленный урок"""
    try:
        lesson_id = int(callback.data.split(":")[1])
        
        lesson_service = LessonService(session)
        user_service = UserService(session)
        
        # Получение урока
        lesson = await lesson_service.get_lesson_by_id(lesson_id)
        
        if not lesson:
            await callback.answer("❌ Урок не найден")
            return
        
        # Проверка доступа
        has_access = await lesson_service.check_user_has_lesson(
            callback.from_user.id, 
            lesson_id
        )
        
        if not has_access and not lesson.is_free:
            await callback.answer("❌ У вас нет доступа к этому уроку")
            return
        
        # Увеличение счетчика просмотров
        await lesson_service.increment_lesson_views(lesson_id)
        
        # Логирование открытия урока
        await user_service.log_user_activity(
            callback.from_user.id, 
            "open_lesson", 
            lesson_id=lesson_id
        )
        
        # Показ контента урока
        await show_lesson_content(callback, lesson, session)
        
    except (ValueError, IndexError):
        await callback.answer("❌ Некорректный ID урока")
    except Exception as e:
        logger.error(f"Ошибка при открытии урока: {e}")
        await callback.answer("❌ Произошла ошибка при открытии урока")


async def show_lesson_content(callback: CallbackQuery, lesson, session: AsyncSession):
    """Показать контент урока"""
    try:
        # Заголовок урока
        content_header = f"""
▶️ <b>{lesson.title}</b>

📚 <b>Содержание урока:</b>
"""
        
        # В зависимости от типа контента
        if lesson.content_type == "video" and lesson.file_id:
            # Отправка видео
            await callback.message.answer_video(
                video=lesson.file_id,
                caption=f"{content_header}\n🎥 Видеоурок готов к просмотру!"
            )
        elif lesson.content_type == "photo" and lesson.file_id:
            # Отправка фото
            await callback.message.answer_photo(
                photo=lesson.file_id,
                caption=f"{content_header}\n📸 Изучайте материал внимательно!"
            )
        elif lesson.content_type == "document" and lesson.file_id:
            # Отправка документа
            await callback.message.answer_document(
                document=lesson.file_id,
                caption=f"{content_header}\n📄 Документ готов к изучению!"
            )
        elif lesson.content_type == "audio" and lesson.file_id:
            # Отправка аудио
            await callback.message.answer_audio(
                audio=lesson.file_id,
                caption=f"{content_header}\n🎵 Аудиоурок готов к прослушиванию!"
            )
        else:
            # Текстовый контент
            text_content = f"""
{content_header}

📖 <b>Материал урока:</b>

{lesson.description}

<i>✅ Урок успешно открыт! Изучайте материал в удобном темпе.</i>
"""
            
            await callback.message.edit_text(text_content)
        
        # Кнопки завершения урока
        from keyboards.user import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        
        builder.row(InlineKeyboardButton(
            text="✅ Урок изучен", 
            callback_data="lesson_completed"
        ))
        
        builder.row(
            InlineKeyboardButton(text="👤 Мои уроки", callback_data="my_purchases"),
            InlineKeyboardButton(text="📚 К каталогу", callback_data="catalog")
        )
        
        builder.row(InlineKeyboardButton(
            text="🏠 Главное меню", 
            callback_data="main_menu"
        ))
        
        # Отправка кнопок управления (если контент не текстовый)
        if lesson.file_id:
            await callback.message.answer(
                "🎯 <b>Управление уроком:</b>",
                reply_markup=builder.as_markup()
            )
        
        await callback.answer("✅ Урок открыт!")
        
    except Exception as e:
        logger.error(f"Ошибка при показе контента урока: {e}")
        await callback.answer("❌ Произошла ошибка при загрузке контента")