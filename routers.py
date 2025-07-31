from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from models import User, UserCreate, UserResponse
from db import get_db


router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/users", response_model=UserResponse)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    db_user = User(**user.model_dump())
    db.add(db_user)
    await db.commit()
    print("id = ",db_user.id)
    await db.refresh(db_user)
    print("id = ",db_user.id)
  
    return UserResponse(id=db_user.id, name=db_user.name, email=db_user.email)

@router.get("/users/all_users", response_model=list[UserResponse])
async def get_all_users(db: AsyncSession = Depends(get_db)):
    users = (await db.execute(select(User))).scalars().all()
    return users


@router.delete("/users/all_users")
async def delete_all_users(db: AsyncSession = Depends(get_db)):
    await db.execute(delete(User))
    await db.commit()
    return {"detail": "All users successfully deleted"}
