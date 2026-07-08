from database import db
from models import Base
import asyncio
from sqlalchemy import text

async def migrate_database():
    """Добавляет новую колонку last_bonus_at в таблицу users"""
    async with db.engine.begin() as conn:
        # Проверяем, существует ли колонка last_bonus_at
        result = await conn.execute(
            text("PRAGMA table_info(users)")
        )
        columns = [row[1] for row in result]
        
        if 'last_bonus_at' not in columns:
            print("Добавляем колонку last_bonus_at в таблицу users...")
            await conn.execute(
                text("ALTER TABLE users ADD COLUMN last_bonus_at DATETIME")
            )
            print("Колонка last_bonus_at успешно добавлена!")
        else:
            print("Колонка last_bonus_at уже существует")

if __name__ == '__main__':
    asyncio.run(migrate_database())