"""Загальні (спільні для всіх модулів) елементи ORM.

Моделі конкретних блюпринтів лежать поруч із ними (наприклад, app/posts/models.py).
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Базовий клас для всіх моделей (SQLAlchemy 2.0, декларативний стиль)."""
