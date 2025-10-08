from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean, DateTime, Table, Time
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

# --- Таблица связи примеров и уровней ---
example_levels = Table(
    "example_levels",
    Base.metadata,
    Column("example_id", Integer, ForeignKey("examples.id")),
    Column("level_id", Integer, ForeignKey("levels.id"))
)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String)
    role = Column(String, default="user")
    created_at = Column(DateTime, default=datetime.utcnow)

    example_stats = relationship("UserExampleStat", back_populates="user")
    category_stats = relationship("UserCategoryStat", back_populates="user")
    settings = relationship("UserSettings", uselist=False, back_populates="user")


class AccessCode(Base):
    __tablename__ = "access_codes"

    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    is_used = Column(Boolean, default=False)
    used_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Level(Base):
    __tablename__ = "levels"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

    examples = relationship("Example", secondary=example_levels, back_populates="levels")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

    examples = relationship("Example", back_populates="category")
    user_stats = relationship("UserCategoryStat", back_populates="category")


class Example(Base):
    __tablename__ = "examples"

    id = Column(Integer, primary_key=True)
    sentence = Column(Text, nullable=False)
    explanation = Column(Text)
    category_id = Column(Integer, ForeignKey("categories.id"))
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    category = relationship("Category", back_populates="examples")
    levels = relationship("Level", secondary=example_levels, back_populates="examples")
    answers = relationship("Answer", back_populates="example")
    user_stats = relationship("UserExampleStat", back_populates="example")


class Answer(Base):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True)
    example_id = Column(Integer, ForeignKey("examples.id"))
    text = Column(Text, nullable=False)
    is_correct = Column(Boolean, default=False)

    example = relationship("Example", back_populates="answers")


class UserCategoryStat(Base):
    __tablename__ = "user_category_stats"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    category_id = Column(Integer, ForeignKey("categories.id"), primary_key=True)

    correct_attempts = Column(Integer, default=0)
    total_attempts = Column(Integer, default=0)

    user = relationship("User", back_populates="category_stats")
    category = relationship("Category", back_populates="user_stats")


class UserExampleStat(Base):
    __tablename__ = "user_example_stats"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    example_id = Column(Integer, ForeignKey("examples.id"), primary_key=True)

    correct_attempts = Column(Integer, default=0)
    total_attempts = Column(Integer, default=0)

    user = relationship("User", back_populates="example_stats")
    example = relationship("Example", back_populates="user_stats")

class UserSettings(Base):
    __tablename__ = "user_settings"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    answers_count = Column(Integer, nullable=True)
    examples_count = Column(Integer, nullable=True)
    language_level = Column(Integer, ForeignKey("levels.id"), nullable=True)
    training_time = Column(Time, nullable=True)

    user = relationship("User", back_populates="settings")
    level = relationship("Level")