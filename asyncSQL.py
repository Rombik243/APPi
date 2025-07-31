from pydantic import BaseModel 
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import String, Integer, select
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import FastAPI, Depends, HTTPException
from contextlib import asynccontextmanager
import routers as users_router
import uvicorn

from fastapi import APIRouter
from db import lifespan
import family as family_router



from models import Parent, Child, ParentChildAssociation, ParentResponse, Family
from db import get_db
from family import create_family
app = FastAPI(lifespan=lifespan)


@app.get("/")
async def read_root():
    return {"Hello": "World"}



@app.get("/test-family")
async def test_family_creation(db: AsyncSession = Depends(get_db)):
    # Создаем тестовые данные
    parent1 = Parent(name="Тест Родитель 1")
    parent2 = Parent(name="Тест Родитель 2")
    child1 = Child(name="Тест Ребенок 1")
    child2 = Child(name="Тест Ребенок 2")

    db.add_all([parent1, parent2, child1, child2])
    await db.commit()

    # Создаем объект Family для теста
    class Test:
        parent1 = parent1.id
        parent2 = parent2.id
        children = [child1.id, child2.id]

    # Вызываем вашу функцию
    result = await create_family(Fam(), db)

    # Возвращаем результаты проверки
    test_parent = await db.get(Parent, parent1.id)
    test_child = await db.get(Child, child1.id)

    return {
        "function_result": result,
        "parent1_children_count": len(test_parent.children),
        "child1_parents_count": len(test_child.parents)
    }



app.include_router(users_router.router)
app.include_router(family_router.router)
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
