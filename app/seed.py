"""CLI-команда `flask seed-lab8`: тестові дані для лабораторної 8 (п. 13)."""

import click

from app import db
from app.posts.models import Post, Tag
from app.users.models import User


def register_commands(app):
    @app.cli.command("seed-lab8")
    def seed_lab8():
        """Додає 2 авторів, 3 теги і 5 постів (ідемпотентно: якщо автори вже є — нічого не робить)."""
        if db.session.scalar(db.select(User).where(User.username == "user1")):
            click.echo("Тестові дані вже є — пропускаю.")
            return

        users = []
        for name in ("user1", "user2"):
            u = User(username=name, email=f"{name}@ex.com")
            u.set_password("12345")
            users.append(u)
        tech, art, science = (Tag(name=n) for n in ("Tech", "Art", "Science"))
        db.session.add_all([*users, tech, art, science])

        # (заголовок, автор, теги): один пост має кілька тегів, а тег Tech — у кількох постах
        rows = [
            ("Art of pop culture", users[0], [tech, art, science]),
            ("Python tips", users[0], [tech]),
            ("Museum notes", users[1], [art]),
            ("Space news", users[1], [science, tech]),
            ("Weekend reading", users[0], [art, science]),
        ]
        for title, author, tags in rows:
            db.session.add(Post(title=title, content=f"Content of {title}", category="tech",
                                user=author, tags=tags))
        db.session.commit()
        click.echo("Створено: 2 авторів, 3 теги, 5 постів.")
