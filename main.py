from pydantic import BaseModel, Field, field_validator
from fastapi import FastAPI, HTTPException
from datetime import datetime
from typing import Optional
import sqlite3
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy import select, insert
import asyncio

# Асинхронный движок для SQLite (aiosqlite)
engine = create_async_engine("sqlite+aiosqlite:///mydatabase.db")
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    pass


# 1. Подключаемся к базе (файл появится автоматически)


# Модель для SQLAlchemy
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

engine = create_engine("sqlite:///tasks.db")  # Файл tasks.db появится автоматически

app = FastAPI()

# Создание таблиц при старте


# Pydantic модели
class TaskSchema(BaseModel):
    id: int = Field(ge=0)
    category: Optional[str] = None
    title: str = Field(max_length=70)
    description: str = Field(max_length=1000)
    status: bool
    priority: Optional[int] = None
    deadline: Optional[str] = None
    percent: int = Field(ge=0, le=100)

    @field_validator('deadline')
    def validate_deadline(cls, value):
        if value is None:
            return value
        try:
            datetime.strptime(value, "%Y-%d-%m")
            return value
        except ValueError:
            raise ValueError("Invalid date format. Use YYYY-DD-MM")

# Эндпоинты
@app.post("/tasks", response_model=TaskSchema)
async def create_task(task: TaskSchema):
    async with async_session() as session:
        try:
            result = await session.execute(
                insert(Task).values(**task.model_dump())
            )
            await session.commit()
            return task
        except Exception as e:
            await session.rollback()
            raise HTTPException(status_code=400, detail=str(e))

@app.get("/tasks", response_model=list[TaskSchema])
async def get_tasks():
    async with async_session() as session:
        result = await session.execute(select(Task))
        tasks = result.scalars().all()
        return tasks

@app.get("/tasks/alltasks")
async def get_all_tasks():
    async with async_session() as session:
        try:
            # Выполняем обычный SQL-запрос
            result = await session.execute(text("SELECT * FROM tasks"))

            # Получаем все записи
            tasks = result.mappings().all()

            # Преобразуем в список словарей
            tasks_list = [dict(task) for task in tasks]

            return {
                "status": "success",
                "data": tasks_list,
                "count": len(tasks_list)
            }

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Database error: {str(e)}"
            )
    

@app.get("/")
async def read_root():
    return {"Hello": "World"}

# Для запуска
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)




