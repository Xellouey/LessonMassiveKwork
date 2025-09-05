"""
Тест удаления кнопки "Мои достижения"
"""
import sys
sys.path.insert(0, '.')

def test_achievements_button_removal():
    """Тестирование удаления кнопки достижений"""
    print("🧪 Тестирование удаления кнопки 'Мои достижения'...")
    
    # Читаем файл
    try:
        with open('handlers/user/free_lessons.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверяем, что кнопка удалена
        if "Мои достижения" in content:
            print("❌ Кнопка 'Мои достижения' все еще найдена в коде!")
            return False
        
        if "achievements" in content:
            print("❌ Callback 'achievements' все еще найден в коде!")
            return False
        
        print("✅ Кнопка 'Мои достижения' успешно удалена!")
        print("✅ Callback 'achievements' больше не используется!")
        
        # Проверяем, что остались правильные кнопки
        if "Открыть каталог" in content and "Главное меню" in content:
            print("✅ Остальные кнопки на месте!")
        else:
            print("⚠️ Возможно, удалены и другие кнопки")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при чтении файла: {e}")
        return False

if __name__ == "__main__":
    success = test_achievements_button_removal()
    
    if success:
        print("\n🎉 Тест пройден успешно!")
        print("\n📝 Изменения:")
        print("• ❌ Удалена кнопка '🏆 Мои достижения'")  
        print("• ❌ Удален callback 'achievements'")
        print("• ✅ Оставлены кнопки 'Открыть каталог' и 'Главное меню'")
        print("\n🚀 Теперь в уроке 'Как эффективно учиться с нашим ботом' нет кнопки достижений!")
    else:
        print("\n❌ Тест не пройден, проверьте изменения.")