import sqlite3

# Подключение к базе данных
conn = sqlite3.connect('learning_bot.db')
cursor = conn.cursor()

# Получение списка таблиц
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print('Tables in database:')
for table in tables:
    print(f'- {table[0]}')

# Закрытие соединения
conn.close()