from datetime import datetime, timezone

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app import db
from app.users.models import User  # noqa: F401  (потрібен для relationship)

CATEGORY_VALUES = ("news", "publication", "tech", "other")


def utcnow():
    """Поточний UTC-час без tzinfo (аналог datetime.utcnow(), який застарів з Python 3.12)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


# Асоціативна таблиця для зв'язку "багато-до-багатьох" між Post і Tag
post_tags = db.Table(
    "post_tags",
    sa.Column("post_id", sa.ForeignKey("posts.id"), primary_key=True),
    sa.Column("tag_id", sa.ForeignKey("tags.id"), primary_key=True),
)


class Post(db.Model):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(sa.String(150))
    content: Mapped[str] = mapped_column(sa.Text)
    posted: Mapped[datetime] = mapped_column(default=utcnow)
    category: Mapped[str] = mapped_column(
        sa.Enum(*CATEGORY_VALUES, name="post_category"), default="other"
    )
    # server_default дозволяє додати NOT NULL-стовпці до вже заповненої таблиці (міграція)
    is_active: Mapped[bool] = mapped_column(default=True, server_default=sa.true())
    # Автор поста: зв'язок "один-до-багатьох" (один User -> багато Post).
    # nullable — щоб існуючі пости без автора не ламали міграцію.
    user_id: Mapped[int | None] = mapped_column(sa.ForeignKey("users.id"))
    user: Mapped["User | None"] = relationship(back_populates="posts")

    # Теги: "багато-до-багатьох" через асоціативну таблицю post_tags
    tags: Mapped[list["Tag"]] = relationship(secondary=post_tags, back_populates="posts")

    def __repr__(self):
        return f"<Post(id={self.id}, title={self.title!r})>"


class Tag(db.Model):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(sa.String(50), unique=True)

    posts: Mapped[list["Post"]] = relationship(secondary=post_tags, back_populates="tags")

    def __repr__(self):
        return f"<Tag(id={self.id}, name={self.name!r})>"
