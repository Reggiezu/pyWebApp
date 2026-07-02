from typing import Optional
from datetime import datetime
from sqlalchemy import String, DateTime, func, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from flask_sqlalchemy import SQLAlchemy

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)


class User(Base):
    __tablename__ = "users"
    # Primary Key (Infers Integer)
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Non-nullable String with explicit length (Infers VARCHAR(50), NOT NULL)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    
    # Column with a server-side default value
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )

class ScoreCard(Base):
    __tablename__ = "scorecards"
    # Primary Key (Infers Integer)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    week_number : Mapped[int] = mapped_column(default=0)
    reflection_week: Mapped[str] = mapped_column(default="")

    # Column with a server-side default value
    created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), 
    server_default=func.now()
        )

class Category(Base):
    __tablename__ = "categories"
    # Primary Key (Infers Integer)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    name: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(String(250))
    # Column with a server-side default value
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )

class Goal(Base):
    __tablename__ = "goals"
    # Primary Key (Infers Integer)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    name: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(String(250))
    # Column with a server-side default value
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )

class ScorecardInit(Base):
    __tablename__ = "scorecardInit"
    # Primary Key (Infers Integer)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    scoreCard_id: Mapped[int] = mapped_column(ForeignKey('scorecards.id'))
    category_id: Mapped[int] = mapped_column(ForeignKey('categories.id'))
    goal_id: Mapped[int] = mapped_column(ForeignKey('goals.id'))
    reflection: Mapped[str] = mapped_column(default="")
    description: Mapped[str] = mapped_column(default="")
    rules: Mapped[str] = mapped_column(String(250))
    # Column with a server-side default value
    created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), 
    server_default=func.now()
        )
    
class WeeklyCategoryScore(Base):
    __tablename__ = "weekly_category_score"
    # Primary Key (Infers Integer)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    scoreCard_id: Mapped[int] = mapped_column(ForeignKey('scorecards.id'))
    category_id: Mapped[int] = mapped_column(ForeignKey('categories.id'))
    week_number : Mapped[int] = mapped_column(default=0)
    category_percentage : Mapped[int] = mapped_column(default=0)
    # Column with a server-side default value
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )