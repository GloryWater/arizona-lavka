"""
Скрипт для создания первого администратора.

Использование:
    python create_admin.py <username> <email> <password>

Пример:
    python create_admin.py admin admin@example.com SecurePassword123
"""

"""
Arizona Lavka Marketplace - Admin User Creator.

© 2026 Arizona Lavka Marketplace. All Rights Reserved.
License: Proprietary Commercial License
"""

import asyncio
import sys
import os

# Добавляем родительскую директорию в path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from database import Base, User
from services.auth_service import PasswordHandler


async def create_admin(username: str, email: str, password: str):
    """Создаёт пользователя с ролью admin."""
    
    # URL базы данных (должен совпадать с .env)
    database_url = "postgresql+asyncpg://arizonalavka:arizonalavka_password@postgres:5432/arizonalavka"
    
    # Для локального тестирования с SQLite
    if not os.environ.get("USE_POSTGRES"):
        database_url = "sqlite+aiosqlite:///./test_admin.db"
        print("⚠️  Используется SQLite для тестирования (файл: test_admin.db)")
    
    # Создаём движок
    engine = create_async_engine(database_url, echo=True)
    
    # Создаём таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Создаём сессию
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Проверяем существует ли пользователь
        result = await session.execute(select(User).where(User.username == username))
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print(f"❌ Пользователь '{username}' уже существует!")
            return False
        
        # Создаём админа
        admin_user = User(
            username=username,
            email=email,
            hashed_password=PasswordHandler.hash(password),
            role="admin",
            first_name="Admin",
            last_name="User",
        )
        
        session.add(admin_user)
        await session.commit()
        
        print(f"✅ Администратор '{username}' успешно создан!")
        print(f"   ID: {admin_user.id}")
        print(f"   Email: {admin_user.email}")
        print(f"   Роль: {admin_user.role}")
        print(f"\n🔐 Теперь вы можете войти в админ-панель: /admin")
        
        return True


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Использование: python create_admin.py <username> <email> <password>")
        print("Пример: python create_admin.py admin admin@example.com SecurePassword123")
        sys.exit(1)
    
    username = sys.argv[1]
    email = sys.argv[2]
    password = sys.argv[3]
    
    if len(password) < 8:
        print("❌ Пароль должен быть не менее 8 символов!")
        sys.exit(1)
    
    asyncio.run(create_admin(username, email, password))
