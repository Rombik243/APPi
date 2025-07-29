from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker, Mapped, mapped_column, Session    
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn


# Настройка подключения к SQLite (файл mydb.db)
engine = create_engine("sqlite:///mydatab.db")
Base = declarative_base()  # ← База для моделей
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def get_db():
    # Этап 1: Создание сессии (при вызове Depends(get_db))
    db = SessionLocal()  # ← Сессия открыта

    try:
        # Этап 2: Передача сессии в эндпоинт
        yield db  # ← Сессия "заморожена" и используется в запросе

    finally:
        # Этап 3: Закрытие сессии (после завершения эндпоинта)
        db.close()  # ← Сессия закрыта

# Описываем таблицу "users" как класс
class User(Base):
    __tablename__ = "users"
    id : Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name : Mapped[str]
    email : Mapped[str]
    password : Mapped[str]

# Создаём таблицы в БД
Base.metadata.create_all(engine)

app = FastAPI()

# Схема для создания (клиент → сервер)
class UserCreate(BaseModel):
    name: str
    email: str
    password: str  # В реальном проекте хэшируйте!

# Схема для ответа (сервер → клиент)
class UserResponse(BaseModel):
    id: int  # Добавляем id, который вернёт БД
    name: str
    email: str
        

@app.post("/users", response_model = UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(name = user.name, email = user.email, password = user.password)

    db.add(db_user)
    db.commit()
    db.refresh(db_user) # Refresh the object to get the id
    return UserResponse(id=db_user.id, name=db_user.name, email=db_user.email)
    
@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/users/all_users", response_model=list[UserResponse])
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(User).all()

    if not users:
        raise HTTPException(status_code=404, detail="User not found")

    return users

@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user

@app.delete("/users/{user_id}")  # ← Добавлен / перед users
def delete_user(user_id: int, db: Session = Depends(get_db)):
    deleted_count = db.query(User).filter(User.id == user_id).delete()
    db.commit()

    if not deleted_count:  # Более питонический вариант проверки
        raise HTTPException(
            status_code=404,
            detail=f"User with ID {user_id} not found"
        )

    return {"detail": f"User {user_id} successfully deleted"}

#обновление данных
@app.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).get(user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    db_user.name = user.name
    db_user.email = user.email
    db_user.password = user.password
    db.commit()
    db.refresh(db_user)
    return UserResponse(id=db_user.id, name=db_user.name, email=db_user.email)


# @app.delete("/users/{user_id}")
# def del_user(user_id: int, )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

