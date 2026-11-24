"""Flask-WTF форми блюпринта posts."""

from datetime import datetime

from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    SelectField,
    SelectMultipleField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.fields import DateTimeLocalField
from wtforms.validators import DataRequired, Length

from app import db
from app.users.models import User

from .models import Tag

CATEGORIES = [
    ("news", "Новина"),
    ("publication", "Публікація"),
    ("tech", "Технології"),
    ("other", "Інше"),
]
CATEGORY_LABELS = dict(CATEGORIES)


def _strip(value):
    return value.strip() if isinstance(value, str) else value


class PostForm(FlaskForm):
    title = StringField(
        "Заголовок",
        filters=[_strip],
        validators=[
            DataRequired(message="Вкажіть заголовок."),
            Length(min=2, max=150, message="Заголовок має містити від 2 до 150 символів."),
        ],
    )
    content = TextAreaField(
        "Текст",
        filters=[_strip],
        validators=[DataRequired(message="Введіть текст поста.")],
        render_kw={"rows": 5, "cols": 40},
    )
    is_active = BooleanField("Активний пост", default=True)
    publish_date = DateTimeLocalField(
        "Дата публікації",
        format=["%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S"],
        default=datetime.now,
        validators=[DataRequired(message="Вкажіть дату і час публікації.")],
    )
    category = SelectField(
        "Категорія",
        choices=CATEGORIES,
        validators=[DataRequired(message="Оберіть категорію.")],
    )
    # варіанти вибору заповнюються з БД у __init__ (синтаксис SQLAlchemy 2.0)
    author_id = SelectField(
        "Автор",
        coerce=int,
        validators=[DataRequired(message="Оберіть автора.")],
    )
    tags = SelectMultipleField("Теги", coerce=int)
    submit = SubmitField("Зберегти")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        users = db.session.scalars(db.select(User).order_by(User.id)).all()
        self.author_id.choices = [(u.id, u.username) for u in users]
        all_tags = db.session.scalars(db.select(Tag).order_by(Tag.name)).all()
        self.tags.choices = [(t.id, t.name) for t in all_tags]


class DeleteForm(FlaskForm):
    """Порожня форма: потрібна лише для CSRF-токена при видаленні."""
