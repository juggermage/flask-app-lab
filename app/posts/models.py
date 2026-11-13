from datetime import datetime, timezone

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app import db

CATEGORY_VALUES = ("news", "publication", "tech", "other")


def utcnow():
    """Поточний UTC-час без tzinfo (аналог datetime.utcnow(), який застарів з Python 3.12)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


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
    author: Mapped[str] = mapped_column(
        sa.String(20), default="Anonymous", server_default="Anonymous"
    )

    def __repr__(self):
        return f"<Post(id={self.id}, title={self.title!r})>"
