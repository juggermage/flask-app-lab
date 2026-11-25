"""ORM-моделі блюпринта users (лабораторна 8)."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash

from app import db, bcrypt, login_manager
from flask_login import UserMixin


@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except (ValueError, TypeError):
        return None


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(sa.String(50), unique=True)
    email: Mapped[str] = mapped_column(sa.String(120), unique=True)
    # зберігаємо хеш пароля, а не сам пароль
    password: Mapped[str] = mapped_column(sa.String(255))

    # delete-orphan: при видаленні користувача видаляються і його пости
    posts: Mapped[list["Post"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def set_password(self, raw_password: str) -> None:
        self.password = bcrypt.generate_password_hash(raw_password).decode("utf-8")

    def check_password(self, raw_password: str) -> bool:
        if len(raw_password.encode("utf-8")) > 72:
            return False
        if self.password.startswith(("$2a$", "$2b$", "$2y$")):
            return bcrypt.check_password_hash(self.password, raw_password)
        # Сумісність із хешами Werkzeug з лабораторної 8.
        return check_password_hash(self.password, raw_password)

    def __repr__(self):
        return f"User('{self.email}')"
