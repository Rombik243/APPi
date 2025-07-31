from db import Base
from sqlalchemy import String, Integer, ForeignKey, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship 
from pydantic import BaseModel


class User(Base):
  __tablename__ = "users"
  id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
  name: Mapped[str] = mapped_column(String(100))
  email: Mapped[str] = mapped_column(String(100))
  password: Mapped[str] = mapped_column(String(50))
  image: Mapped[str] = mapped_column(String(150))

class UserCreate(BaseModel):
  name: str
  email: str
  password: str
  image: str

class UserResponse(BaseModel):
  id: int
  name: str
  email: str

class ParentResponse(BaseModel):
  id: int
  name: str

class ChildResponse(BaseModel):
  id: int
  name: str

class Family(BaseModel):
  parent1: int
  parent2: int | None
  children: list[int] | None

class LinkResponse(BaseModel):
  parent_id: int
  child_id: int

# association_table = Table(
#     "association",
#     Base.metadata,
#     mapped_column("children_id", ForeignKey("parents.id")),
#     mapped_column("parents_id", ForeignKey("children.id"))
# )

class ParentChildAssociation(Base):
  __tablename__ = "association"

  parent_id: Mapped[int] = mapped_column(ForeignKey("parents.id"), primary_key=True)
  child_id: Mapped[int] = mapped_column(ForeignKey("children.id"), primary_key=True)

  class Config:
    from_attributes = True

class Parent(Base):
  __tablename__ = "parents"

  id: Mapped[int] = mapped_column(Integer, primary_key=True)
  name: Mapped[str] = mapped_column(String(50))
  children = relationship(
      "Child",
      secondary="association",  # Используем имя таблицы как строку
      back_populates="parents",
      viewonly=False  # Разрешаем изменения через связь
  )
  class Config:
    from_attributes = True

class Child(Base):
  __tablename__ = "children"

  id: Mapped[int] = mapped_column(Integer, primary_key=True)
  name: Mapped[str] = mapped_column(String(50))
  parents = relationship(
      "Parent",
      secondary="association",  # Используем имя таблицы как строку
      back_populates="children",
      viewonly=False
  )


