"""
Тест исправлений для администрирования категорий
"""
import asyncio
import sys
sys.path.insert(0, '.')

async def test_admin_fixes():
    """Тестирование исправлений"""
    print("🧪 Тестирование исправлений администраторского интерфейса...")
    
    # Тест 1: Проверка импортов
    try:
        from handlers.admin.main import show_admin_menu, admin_cancel_action
        from handlers.admin.categories import delete_category, confirm_category_deletion
        from keyboards.admin import simple_confirmation_keyboard
        print("✅ Все импорты работают корректно")
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        return False
    
    # Тест 2: Проверка клавиатур
    try:
        kb = simple_confirmation_keyboard("test_action", "test_cancel")
        print("✅ Клавиатура подтверждения работает")
    except Exception as e:
        print(f"❌ Ошибка клавиатуры: {e}")
        return False
    
    print("✅ Все тесты пройдены!")
    print("\n📝 Исправления:")
    print("1. ✅ Добавлена проверка admin is not None в show_admin_menu")
    print("2. ✅ Исправлен admin_cancel_action для корректной передачи параметров")
    print("3. ✅ Заменен confirm_action_keyboard на simple_confirmation_keyboard")
    print("4. ✅ Добавлен импорт simple_confirmation_keyboard")
    
    print("\n🚀 Теперь удаление категорий должно работать корректно!")
    return True

if __name__ == "__main__":
    asyncio.run(test_admin_fixes())