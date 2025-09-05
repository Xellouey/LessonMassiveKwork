"""
Обработчики редактирования текстов интерфейса для административной панели
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from services.text import TextService
from keyboards.admin import (
    text_categories_keyboard, text_settings_keyboard, text_actions_keyboard,
    back_to_admin_keyboard, text_language_keyboard, text_search_keyboard
)
from states.admin import TextEditingStates
from middlewares.admin import AdminOnlyMiddleware

logger = logging.getLogger(__name__)
router = Router()
router.callback_query.middleware(AdminOnlyMiddleware())
router.message.middleware(AdminOnlyMiddleware())


@router.callback_query(F.data == "admin_texts")
async def show_text_editor_menu(callback: CallbackQuery):
    """Показать меню редактора текстов"""
    try:
        text = """
📝 <b>Редактор текстов интерфейса</b>

Здесь вы можете управлять всеми текстовыми сообщениями, кнопками и уведомлениями бота.

📂 <b>Категории текстов:</b>
• Сообщения - приветствие, помощь, информация
• Кнопки - названия кнопок интерфейса
• Ошибки - сообщения об ошибках
• Успех - уведомления об успешных действиях

🌐 <b>Поддержка языков:</b> Русский, Английский

Выберите действие:
"""

        await callback.message.edit_text(
            text,
            reply_markup=text_categories_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка при показе меню редактора текстов: {e}")
        await callback.answer("Произошла ошибка при загрузке меню")


@router.callback_query(F.data.startswith("text_category:"))
async def show_texts_by_category(callback: CallbackQuery, session: AsyncSession):
    """Показать тексты по категории"""
    try:
        category = callback.data.split(":")[1]
        
        text_service = TextService(session)
        texts = await text_service.get_text_settings_by_category(category)
        
        # Названия категорий для отображения
        category_names = {
            "messages": "Сообщения",
            "buttons": "Кнопки",
            "errors": "Ошибки",
            "success": "Успешные действия",
            "descriptions": "Описания"
        }
        
        category_name = category_names.get(category, category.capitalize())
        
        if not texts:
            text = f"""
📂 <b>Категория: {category_name}</b>

📭 В этой категории пока нет текстов.
Создайте первый текст, чтобы увидеть его здесь.
"""
            await callback.message.edit_text(
                text,
                reply_markup=back_to_admin_keyboard(),
                parse_mode="HTML"
            )
        else:
            text = f"📂 <b>Категория: {category_name}</b>\n\nВсего текстов: {len(texts)}\n\nВыберите текст для редактирования:\n\n"
            
            await callback.message.edit_text(
                text,
                reply_markup=text_settings_keyboard(texts, category),
                parse_mode="HTML"
            )
        
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка при получении текстов категории {category}: {e}")
        await callback.answer("Ошибка при загрузке текстов категории")


@router.callback_query(F.data.startswith("edit_text:"))
async def show_text_details(callback: CallbackQuery, session: AsyncSession):
    """Показать детали текста для редактирования"""
    try:
        text_key = callback.data.split(":")[1]
        
        text_service = TextService(session)
        text_setting = await text_service.get_text_setting_by_key(text_key)
        
        if not text_setting:
            await callback.answer("❌ Текст не найден")
            return
        
        # Показываем информацию о тексте
        text = f"""
📝 <b>Редактирование текста</b>

🔑 <b>Ключ:</b> <code>{text_setting.key}</code>
📂 <b>Категория:</b> {text_setting.category}
📋 <b>Описание:</b> {text_setting.description or 'Не задано'}

🇷🇺 <b>Русский текст:</b>
{text_setting.value_ru}

🇬🇧 <b>Английский текст:</b>
{text_setting.value_en or 'Не задан'}

⏰ <b>Последнее обновление:</b> {text_setting.updated_at.strftime('%d.%m.%Y %H:%M') if text_setting.updated_at else 'Неизвестно'}

Выберите действие:
"""

        await callback.message.edit_text(
            text,
            reply_markup=text_actions_keyboard(text_key),
            parse_mode="HTML"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка при получении деталей текста {text_key}: {e}")
        await callback.answer("Ошибка при загрузке деталей текста")


@router.callback_query(F.data.startswith("edit_text_lang:"))
async def start_text_editing(callback: CallbackQuery, state: FSMContext):
    """Начать редактирование текста на выбранном языке"""
    try:
        _, text_key, language = callback.data.split(":")
        
        # Сохраняем данные в состоянии
        await state.set_data({
            'text_key': text_key,
            'language': language
        })
        
        lang_name = "русском" if language == "ru" else "английском"
        
        text = f"""
✏️ <b>Редактирование текста на {lang_name} языке</b>

🔑 <b>Ключ:</b> <code>{text_key}</code>

Введите новый текст:

<i>💡 Поддерживается HTML-форматирование: 
&lt;b&gt;жирный&lt;/b&gt;, &lt;i&gt;курсив&lt;/i&gt;, &lt;code&gt;код&lt;/code&gt;</i>
"""

        await callback.message.edit_text(
            text,
            parse_mode="HTML"
        )
        
        # Устанавливаем состояние для ожидания нового текста
        if language == "ru":
            await state.set_state(TextEditingStates.entering_new_text_ru)
        else:
            await state.set_state(TextEditingStates.entering_new_text_en)
        
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка при начале редактирования текста: {e}")
        await callback.answer("Ошибка при начале редактирования")


@router.message(TextEditingStates.entering_new_text_ru)
async def handle_new_text_ru(message: Message, state: FSMContext, session: AsyncSession):
    """Обработать новый русский текст"""
    try:
        data = await state.get_data()
        text_key = data.get('text_key')
        new_text = message.text
        
        if not new_text or len(new_text.strip()) == 0:
            await message.answer("❌ Текст не может быть пустым. Попробуйте еще раз:")
            return
        
        if len(new_text) > 4000:
            await message.answer(
                "❌ Текст слишком длинный. Максимальная длина: 4000 символов.\n"
                f"Ваш текст: {len(new_text)} символов. Сократите текст и попробуйте еще раз:"
            )
            return
        
        # Обновляем текст
        text_service = TextService(session)
        result = await text_service.update_text_setting(
            key=text_key,
            value_ru=new_text
        )
        
        if result:
            await message.answer(
                f"✅ Русский текст успешно обновлен!\n\n"
                f"🔑 <b>Ключ:</b> <code>{text_key}</code>\n"
                f"📝 <b>Новый текст:</b>\n{new_text}",
                reply_markup=back_to_admin_keyboard(),
                parse_mode="HTML"
            )
            logger.info(f"Обновлен русский текст для ключа {text_key}")
        else:
            await message.answer(
                "❌ Ошибка при обновлении текста. Попробуйте еще раз.",
                reply_markup=back_to_admin_keyboard()
            )
        
        await state.clear()
        
        # Удаляем сообщение пользователя для чистоты интерфейса
        try:
            await message.delete()
        except:
            pass

    except Exception as e:
        logger.error(f"Ошибка при обработке нового русского текста: {e}")
        await message.answer("❌ Произошла ошибка при сохранении текста")
        await state.clear()


@router.message(TextEditingStates.entering_new_text_en)
async def handle_new_text_en(message: Message, state: FSMContext, session: AsyncSession):
    """Обработать новый английский текст"""
    try:
        data = await state.get_data()
        text_key = data.get('text_key')
        new_text = message.text
        
        if not new_text or len(new_text.strip()) == 0:
            await message.answer("❌ Текст не может быть пустым. Попробуйте еще раз:")
            return
        
        if len(new_text) > 4000:
            await message.answer(
                "❌ Текст слишком длинный. Максимальная длина: 4000 символов.\n"
                f"Ваш текст: {len(new_text)} символов. Сократите текст и попробуйте еще раз:"
            )
            return
        
        # Обновляем текст
        text_service = TextService(session)
        result = await text_service.update_text_setting(
            key=text_key,
            value_en=new_text
        )
        
        if result:
            await message.answer(
                f"✅ Английский текст успешно обновлен!\n\n"
                f"🔑 <b>Ключ:</b> <code>{text_key}</code>\n"
                f"📝 <b>Новый текст:</b>\n{new_text}",
                reply_markup=back_to_admin_keyboard(),
                parse_mode="HTML"
            )
            logger.info(f"Обновлен английский текст для ключа {text_key}")
        else:
            await message.answer(
                "❌ Ошибка при обновлении текста. Попробуйте еще раз.",
                reply_markup=back_to_admin_keyboard()
            )
        
        await state.clear()
        
        # Удаляем сообщение пользователя
        try:
            await message.delete()
        except:
            pass

    except Exception as e:
        logger.error(f"Ошибка при обработке нового английского текста: {e}")
        await message.answer("❌ Произошла ошибка при сохранении текста")
        await state.clear()


@router.callback_query(F.data == "admin_text_search")
async def show_text_search_menu(callback: CallbackQuery):
    """Показать меню поиска текстов"""
    try:
        text = """
🔍 <b>Поиск текстов</b>

Введите поисковый запрос для поиска по:
• Ключу текста
• Содержимому (русский/английский)
• Описанию
• Категории

Начните вводить текст для поиска:
"""

        await callback.message.edit_text(
            text,
            reply_markup=back_to_admin_keyboard(),
            parse_mode="HTML"
        )
        
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка при показе меню поиска: {e}")
        await callback.answer("Ошибка при загрузке поиска")


@router.callback_query(F.data == "admin_text_stats")
async def show_text_statistics(callback: CallbackQuery, session: AsyncSession):
    """Показать статистику текстов"""
    try:
        text_service = TextService(session)
        stats = await text_service.get_text_statistics()
        
        if not stats:
            text = """
📊 <b>Статистика текстов</b>

❌ Не удалось загрузить статистику
"""
        else:
            # Формируем распределение по категориям
            category_text = ""
            for category, count in stats.get('category_distribution', {}).items():
                category_text += f"• {category}: {count}\n"
            
            text = f"""
📊 <b>Статистика текстов интерфейса</b>

📈 <b>Общая информация:</b>
• Всего текстов: {stats.get('total_texts', 0)}
• С переводом: {stats.get('texts_with_translation', 0)}
• Категорий: {stats.get('categories_count', 0)}
• Процент переведенных: {stats.get('translation_percentage', 0):.1f}%

📂 <b>Распределение по категориям:</b>
{category_text if category_text else 'Нет данных'}

🌐 <b>Многоязычность:</b>
Поддержка: Русский (основной), Английский
"""
        
        await callback.message.edit_text(
            text,
            reply_markup=back_to_admin_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка при получении статистики текстов: {e}")
        await callback.answer("Ошибка при загрузке статистики")


@router.callback_query(F.data == "admin_text_create")
async def show_text_creation_form(callback: CallbackQuery, state: FSMContext):
    """Показать форму создания нового текста"""
    try:
        text = """
➕ <b>Создание нового текста</b>

Для создания нового текста необходимо указать:

1️⃣ <b>Ключ</b> - уникальный идентификатор (например: welcome_message)
2️⃣ <b>Категория</b> - messages, buttons, errors, success, descriptions
3️⃣ <b>Текст на русском</b> - основной текст
4️⃣ <b>Текст на английском</b> - перевод (необязательно)
5️⃣ <b>Описание</b> - краткое описание назначения (необязательно)

<i>💡 Ключ может содержать только латинские буквы, цифры и подчеркивания</i>

Введите ключ для нового текста:
"""

        await callback.message.edit_text(
            text,
            parse_mode="HTML"
        )
        
        await state.set_state(TextEditingStates.selecting_text_category)
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка при показе формы создания текста: {e}")
        await callback.answer("Ошибка при создании формы")


@router.callback_query(F.data.startswith("delete_text:"))
async def delete_text_setting(callback: CallbackQuery, session: AsyncSession):
    """Удалить настройку текста"""
    try:
        text_key = callback.data.split(":")[1]
        
        text_service = TextService(session)
        success = await text_service.delete_text_setting(text_key)
        
        if success:
            await callback.answer("✅ Текст удален")
            # Возвращаемся к меню редактора текстов
            await show_text_editor_menu(callback)
        else:
            await callback.answer("❌ Не удалось удалить текст")

    except Exception as e:
        logger.error(f"Ошибка при удалении текста {text_key}: {e}")
        await callback.answer("Ошибка при удалении текста")


@router.callback_query(F.data == "admin_text_export")
async def export_texts_for_translation(callback: CallbackQuery, session: AsyncSession):
    """Экспортировать тексты для перевода"""
    try:
        text_service = TextService(session)
        export_data = await text_service.export_texts_for_translation()
        
        if not export_data:
            await callback.message.edit_text(
                "📭 Нет текстов для экспорта",
                reply_markup=back_to_admin_keyboard()
            )
            return
        
        # Формируем текст экспорта (первые 10 записей для демонстрации)
        export_text = "📤 <b>Экспорт текстов для перевода</b>\n\n"
        
        for i, item in enumerate(export_data[:10]):
            export_text += f"🔑 <b>{item['key']}</b>\n"
            export_text += f"📂 {item['category']}\n"
            export_text += f"🇷🇺 {item['value_ru'][:50]}{'...' if len(item['value_ru']) > 50 else ''}\n"
            if item['value_en']:
                export_text += f"🇬🇧 {item['value_en'][:50]}{'...' if len(item['value_en']) > 50 else ''}\n"
            export_text += "\n"
        
        if len(export_data) > 10:
            export_text += f"... и еще {len(export_data) - 10} текстов\n\n"
        
        export_text += f"Всего экспортировано: {len(export_data)} текстов"
        
        await callback.message.edit_text(
            export_text,
            reply_markup=back_to_admin_keyboard(),
            parse_mode="HTML"
        )
        
        logger.info(f"Экспортировано {len(export_data)} текстов для перевода")
        await callback.answer("✅ Экспорт завершен")

    except Exception as e:
        logger.error(f"Ошибка при экспорте текстов: {e}")
        await callback.answer("Ошибка при экспорте текстов")


@router.callback_query(F.data == "admin_text_init")
async def initialize_default_texts(callback: CallbackQuery, session: AsyncSession):
    """Инициализировать тексты по умолчанию"""
    try:
        text_service = TextService(session)
        success = await text_service.initialize_default_texts()
        
        if success:
            await callback.message.edit_text(
                "✅ <b>Тексты по умолчанию инициализированы</b>\n\n"
                "Созданы базовые тексты для:\n"
                "• Приветственных сообщений\n"
                "• Кнопок интерфейса\n" 
                "• Сообщений об ошибках\n"
                "• Уведомлений об успехе\n\n"
                "Вы можете редактировать их в соответствующих категориях.",
                reply_markup=back_to_admin_keyboard(),
                parse_mode="HTML"
            )
            logger.info("Инициализированы тексты по умолчанию")
        else:
            await callback.message.edit_text(
                "❌ Ошибка при инициализации текстов по умолчанию",
                reply_markup=back_to_admin_keyboard()
            )
        
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка при инициализации текстов по умолчанию: {e}")
        await callback.answer("Ошибка при инициализации")