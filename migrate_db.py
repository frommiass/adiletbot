#!/usr/bin/env python3
"""
Миграция БД для Photo News Forwarder
Добавляет новые колонки в существующую таблицу messages
"""

import sqlite3
import sys

DB_PATH = '/opt/adiletbot/messages.db'

def migrate():
    """Добавить новые колонки в таблицу messages"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        print("🔄 Начинаем миграцию БД...")
        
        # Проверяем какие колонки уже есть
        cursor.execute("PRAGMA table_info(messages)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        print(f"✅ Существующие колонки: {existing_columns}")
        
        # Добавляем колонки если их нет
        columns_to_add = [
            ('has_photo', 'BOOLEAN DEFAULT 0'),
            ('total_reactions', 'INTEGER DEFAULT 0'),
            ('is_forwarded', 'BOOLEAN DEFAULT 0'),
            ('forwarded_at', 'DATETIME')
        ]
        
        for column_name, column_type in columns_to_add:
            if column_name not in existing_columns:
                sql = f'ALTER TABLE messages ADD COLUMN {column_name} {column_type}'
                cursor.execute(sql)
                print(f"✅ Добавлена колонка: {column_name}")
            else:
                print(f"⏭️  Колонка {column_name} уже существует")
        
        # Добавляем UNIQUE constraint в reactions если его нет
        print("\n🔄 Проверяем таблицу reactions...")
        cursor.execute("PRAGMA table_info(reactions)")
        print("✅ Таблица reactions существует")
        
        conn.commit()
        conn.close()
        
        print("\n✅ Миграция успешно завершена!")
        print("🚀 Теперь можешь перезапустить бота: systemctl restart adiletbot")
        
    except sqlite3.Error as e:
        print(f"❌ Ошибка миграции: {e}")
        sys.exit(1)

if __name__ == '__main__':
    migrate()
