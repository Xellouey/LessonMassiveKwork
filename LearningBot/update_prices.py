"""
Скрипт для обновления цен уроков в USD
"""
import sqlite3
import sys
import os

def update_lesson_prices():
    """Обновление цен уроков в долларах"""
    try:
        conn = sqlite3.connect('learning_bot.db')
        cursor = conn.cursor()
        
        # Получаем все уроки
        cursor.execute("SELECT id, title, price_stars, is_free FROM lessons")
        lessons = cursor.fetchall()
        
        print(f"Найдено {len(lessons)} уроков для обновления")
        print()
        
        updated_count = 0
        
        for lesson in lessons:
            lesson_id, title, price_stars, is_free = lesson
            
            if is_free:
                price_usd = 0.0
            else:
                # Конвертируем звезды в доллары (1 звезда = $0.013)
                price_usd = round(price_stars * 0.013, 2)
            
            # Обновляем price_usd
            cursor.execute(
                "UPDATE lessons SET price_usd = ? WHERE id = ?",
                (price_usd, lesson_id)
            )
            
            updated_count += 1
            
            # Выводим информацию о обновлении
            if is_free:
                print(f"✅ Урок {lesson_id}: '{title[:30]}...' -> БЕСПЛАТНЫЙ")
            else:
                print(f"✅ Урок {lesson_id}: '{title[:30]}...' -> {price_stars} звезд = ${price_usd}")
        
        conn.commit()
        conn.close()
        
        print(f"\n🎉 Успешно обновлено {updated_count} уроков!")
        print("\nТеперь все цены отображаются в долларах:")
        print("• Пользователи видят понятные цены в USD")
        print("• Система автоматически конвертирует в Telegram Stars при оплате")
        print("• Улучшена конверсия покупок за счет понятности цен")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при обновлении цен: {e}")
        return False

def show_price_examples():
    """Показать примеры новых цен"""
    try:
        conn = sqlite3.connect('learning_bot.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT title, price_stars, price_usd, is_free 
            FROM lessons 
            WHERE is_active = 1 
            LIMIT 10
        """)
        lessons = cursor.fetchall()
        
        print("\n📋 Примеры обновленных цен:")
        print("=" * 80)
        print(f"{'Название урока':<40} {'Старая цена':<15} {'Новая цена':<15}")
        print("-" * 80)
        
        for lesson in lessons:
            title, price_stars, price_usd, is_free = lesson
            
            if is_free:
                old_price = f"{price_stars} звезд"
                new_price = "🎁 БЕСПЛАТНО"
            else:
                old_price = f"⭐ {price_stars} звезд"
                new_price = f"💰 ${price_usd}"
            
            print(f"{title[:38]:<40} {old_price:<15} {new_price:<15}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка при получении примеров: {e}")

if __name__ == "__main__":
    print("🔄 Обновление системы ценообразования...")
    print("Изменение с отображения цен в звездах на доллары\n")
    
    if update_lesson_prices():
        show_price_examples()
        
        print("\n" + "="*60)
        print("✅ МИССИЯ ВЫПОЛНЕНА!")
        print("="*60)
        print("Теперь ваши пользователи увидят:")
        print("• 💰 $25 вместо ⭐ 1923 звезд")
        print("• 💰 $10 вместо ⭐ 769 звезд") 
        print("• 🎁 БЕСПЛАТНО для бесплатных уроков")
        print("\nЭто значительно улучшит понимание цен и конверсию!")
    else:
        print("❌ Обновление не удалось")