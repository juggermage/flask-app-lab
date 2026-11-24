"""Лаб. 8, п. 13: підрахунок SELECT при отриманні дописів.

Запуск (кожен варіант — окремий процес, тобто нова ORM-сесія):
    python scripts/lab8_select_count.py plain       # без .options()
    python scripts/lab8_select_count.py optimized   # joinedload + selectinload

Щоб побачити SQL-журнал у консолі, додайте змінну середовища SQLALCHEMY_ECHO=1.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import event, select
from sqlalchemy.orm import joinedload, selectinload

from app import create_app, db
from app.posts.models import Post

mode = sys.argv[1] if len(sys.argv) > 1 else "plain"
app = create_app()

with app.app_context():
    counter = {"select": 0}

    @event.listens_for(db.engine, "before_cursor_execute")
    def _count(conn, cursor, statement, parameters, context, executemany):
        if statement.lstrip().upper().startswith("SELECT"):
            counter["select"] += 1

    stmt = select(Post).order_by(Post.id.desc())
    if mode == "optimized":
        stmt = stmt.options(joinedload(Post.user), selectinload(Post.tags))

    posts = db.session.scalars(stmt).all()
    for post in posts:
        print(post.title, post.user.username, [tag.name for tag in post.tags])

    print(f"\nРежим: {mode} | Кількість дописів: {len(posts)} | Кількість SELECT: {counter['select']}")
