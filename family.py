from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import List
from models import Parent, Child, ParentChildAssociation, ParentResponse, Family, ChildResponse
from models import LinkResponse
from db import get_db
from sqlalchemy.exc import IntegrityError 

router = APIRouter(prefix="/family", tags=["Relations"])


async def create_family(family: Family, db: AsyncSession = Depends(get_db)):
    children = family.children
    if children is None:
        children = []
    par2 = False
    parent1_id = family.parent1
    parent2_id = family.parent2 if family.parent2 else None
    if parent2_id:
        par2 = True
    if par2:
        for child in children:
            new_association1 = ParentChildAssociation(parent_id=parent1_id, child_id=child)
            new_association2 = ParentChildAssociation(parent_id=parent2_id, child_id=child)
            db.add(new_association1)
            db.add(new_association2)
    else:
        for child in children:
            new_association1 = ParentChildAssociation(parent_id=parent1_id, child_id=child)
            db.add(new_association1)
            
    await db.commit()
    return {"detail": "Family created successfully"}


#План такой: сначала создаем родителя, потом ребенка, потом связь, потом проверяем, что все работает
#Как раз потренирую CRUD запросы с асинхронностью.


@router.post("/create_parent", response_model=ParentResponse)
async def create_parent(name: str, db: AsyncSession = Depends(get_db)):
    parent = Parent(name = name)
    db.add(parent)

    await db.commit()
    await db.refresh(parent)
    return ParentResponse(id=parent.id, name=parent.name)


@router.get("/all_parents", response_model=list[ParentResponse])
async def read_parents(db: AsyncSession = Depends(get_db)):
    parents = (await db.execute(select(Parent))).scalars().all()

    return parents


@router.delete("/all_parents")
async def delete_all_parents(db: AsyncSession = Depends(get_db)):
    await db.execute(delete(Parent))
    await db.commit()
    
    return {"Success": "All parents deleted"}


@router.post("/create_child", response_model=ChildResponse)
async def create_child(name : str, db: AsyncSession = Depends(get_db)):
    child = Child(name=name)
    db.add(child)
    
    await db.commit()
    await db.refresh(child)

    return child

@router.get("/all_children", response_model=list[ChildResponse])
async def read_children(db: AsyncSession = Depends(get_db)):
    children = (await db.execute(select(Child))).scalars().all()

    return children


@router.delete("/all_children")
async def delete_children(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(delete(Child))
        await db.commit()  # Обязательно!
        return {
            "deleted_count": result.rowcount,
            "status": "success"
        }
    except Exception as e:
        await db.rollback()  # Откат при ошибке
        raise HTTPException(500, detail=str(e))


#максимум 2 родителя на одного ребёнка. Детей у каждого родителя может быть сколько угодно.
#между двумя родителями связь не рисую, пока нет необходимости

#Уточнение. Чтобы не переписывать и не раздувать функцию, если у родителя несколько детей,
#То этот запрос просто будет выполняться многократно, массивов в ячейке таблицы нужно избегать
@router.post(
    "/link/{parent_id}/{child_id}", 
    response_model=LinkResponse,
    status_code=status.HTTP_201_CREATED
)
async def link_family(
    parent_id: int, 
    child_id: int, 
    db: AsyncSession = Depends(get_db)
):
    try:
        # Проверка существования родителя
        parent = await db.scalar(select(Parent).where(Parent.id == parent_id))
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent not found"
            )

        # Проверка существования ребенка
        child = await db.scalar(select(Child).where(Child.id == child_id))
        if not child:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Child not found"
            )

        # Проверка существующей связи (опционально)
        existing_link = await db.scalar(
            select(ParentChildAssociation).where(
                ParentChildAssociation.parent_id == parent_id,
                ParentChildAssociation.child_id == child_id
            )
        )
        if existing_link:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Relationship already exists"
            )

        # Создание связи
        link = ParentChildAssociation(
            parent_id=parent_id,
            child_id=child_id
        )
        db.add(link)
        await db.commit()

        return link

    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database integrity error"
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )
    

@router.get("/link/dump", response_model=list[LinkResponse])
async def all_links(db: AsyncSession = Depends(get_db)):
    links = (await db.execute(select(ParentChildAssociation))).scalars().all()
    await db.commit()

    return links


@router.get("/get_children/{parent_id}", response_model=list[ChildResponse])
async def get_children(parent_id: int, db: AsyncSession = Depends(get_db)):
    try:
        parent = await db.get(Parent, parent_id)

        await db.refresh(parent)
        return parent.children

    except Exception as e:
        await db.rollback()
    
