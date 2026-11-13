"""Flask-WTF форми блюпринта posts."""

from datetime import datetime

from flask_wtf import FlaskForm
from wtforms import BooleanField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.fields import DateTimeLocalField
from wtforms.validators import DataRequired, Length

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
    submit = SubmitField("Зберегти")


class DeleteForm(FlaskForm):
    """Порожня форма: потрібна лише для CSRF-токена при видаленні."""
