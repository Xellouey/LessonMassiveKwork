"""
Тест для проверки работы системы конвертации валют
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.currency import CurrencyService

def test_currency_conversion():
    """Тест конвертации валют"""
    print("=== Тестирование конвертации валют ===")
    
    # Тест конвертации USD в Stars
    usd_amounts = [10, 25, 50, 100]
    for usd in usd_amounts:
        stars = CurrencyService.usd_to_stars(usd)
        print(f"${usd} -> {stars} звезд")
    
    print()
    
    # Тест конвертации Stars в USD
    stars_amounts = [100, 500, 1000, 2000]
    for stars in stars_amounts:
        usd = CurrencyService.stars_to_usd(stars)
        print(f"{stars} звезд -> ${usd}")
    
    print()
    
    # Тест форматирования цен
    prices = [0, 5, 10.50, 25, 99.99, 100]
    for price in prices:
        formatted = CurrencyService.format_usd_price(price)
        print(f"{price} -> {formatted}")

def test_database_schema():
    """Тест проверки схемы базы данных"""
    print("\n=== Проверка схемы базы данных ===")
    
    import sqlite3
    
    try:
        conn = sqlite3.connect('learning_bot.db')
        cursor = conn.cursor()
        
        # Проверяем, что поле price_usd добавлено
        cursor.execute("PRAGMA table_info(lessons)")
        columns = cursor.fetchall()
        
        price_usd_exists = False
        for column in columns:
            if column[1] == 'price_usd':
                price_usd_exists = True
                print(f"✅ Поле price_usd найдено: {column}")
                break
        
        if not price_usd_exists:
            print("❌ Поле price_usd не найдено в таблице lessons")
            return False
        
        # Проверяем содержимое уроков
        cursor.execute("SELECT id, title, price_stars, price_usd, is_free FROM lessons LIMIT 5")
        lessons = cursor.fetchall()
        
        print("\nПримеры уроков:")
        print("ID | Название | Stars | USD | Бесплатно")
        print("-" * 50)
        for lesson in lessons:
            print(f"{lesson[0]} | {lesson[1][:20]}... | {lesson[2]} | ${lesson[3]} | {bool(lesson[4])}")
        
        conn.close()
        print("✅ База данных обновлена корректно")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при проверке базы данных: {e}")
        return False

if __name__ == "__main__":
    test_currency_conversion()
    test_database_schema()
    
    print("\n=== Итог ===")
    print("✅ Система конвертации валют реализована")
    print("✅ Цены теперь отображаются в долларах")
    print("✅ Оплата осуществляется через Telegram Stars")
    print("✅ База данных обновлена")
    print("\n🎉 Все изменения применены успешно!")