from pydantic import BaseModel, Field, field_validator
from fastapi import FastAPI, HTTPException
from datetime import datetime
from typing import Optional
import os
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy import select, insert
import asyncio

# Настройки БД
DB_PATH = "mydatabase.db"
DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"

# Инициализация движка
engine = create_async_engine(DATABASE_URL)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

class Base(DeclarativeBase):
    pass

class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[Optional[str]]
    title: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str]
    status: Mapped[bool]
    priority: Mapped[Optional[int]]
    deadline: Mapped[Optional[str]]
    percent: Mapped[int] = mapped_column(default=0)

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    """Инициализация при старте"""
    print("Запуск инициализации БД...")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            print("Таблицы созданы")

        # Проверяем сразу после создания
        await check_db_internal()
    except Exception as e:
        print(f"Ошибка инициализации БД: {e}")
        raise

async def check_db_internal():
    """Внутренняя функция проверки"""
    print("\nПроверка БД...")
    try:
        # Проверка файла
        db_exists = os.path.exists(DB_PATH)
        print(f"Файл БД существует: {db_exists}")

        if not db_exists:
            raise Exception("Файл БД не найден")

        # Проверка таблиц
        async with engine.begin() as conn:
            inspector = await conn.run_sync(lambda c: inspect(c))
            tables = inspector.get_table_names()
            print(f"Найдены таблицы: {tables}")

            if "tasks" not in tables:
                raise Exception("Таблица 'tasks' отсутствует")

        # Тестовый запрос
        async with async_session() as session:
            await session.execute(text("SELECT 1 FROM tasks LIMIT 1"))
            print("Тестовый запрос выполнен успешно")

        return True
    except Exception as e:
        print(f"Ошибка проверки БД: {e}")
        return False

@app.get("/check-db")
async def check_db():
    """Публичный эндпоинт для проверки"""
    try:
        is_ok = await check_db_internal()
        if not is_ok:
            raise HTTPException(status_code=500, detail="Проверка БД не пройдена")

        return {
            "status": "success",
            "db_file": os.path.abspath(DB_PATH),
            "tables": ["tasks"],
            "message": "База данных работает корректно"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка БД: {str(e)}"
        )

@app.post("/tasks")
async def create_task(task: dict):
    """Тестовый метод для создания записи"""
    async with async_session() as session:
        try:
            new_task = Task(**task)
            session.add(new_task)
            await session.commit()
            return {"status": "success", "id": new_task.id}
        except Exception as e:
            await session.rollback()
            raise HTTPException(status_code=400, detail=str(e))

@app.get("/tasks")
async def get_tasks():
    """Получение всех задач"""
    async with async_session() as session:
        result = await session.execute(select(Task))
        tasks = result.scalars().all()
        return {"tasks": [{"id": t.id, "title": t.title} for t in tasks]}

@app.get("/")
async def read_root():
    return {
        "message": "Используйте /check-db для проверки БД",
        "endpoints": [
            {"method": "GET", "path": "/check-db", "desc": "Проверка состояния БД"},
            {"method": "POST", "path": "/tasks", "desc": "Создать задачу"},
            {"method": "GET", "path": "/tasks", "desc": "Список задач"}
        ]
    }

if __name__ == "__main__":
    import uvicorn
    print(f"\nЗапуск сервера. БД: {os.path.abspath(DB_PATH)}")
    uvicorn.run(app, host="0.0.0.0", port=8000)
