"""Flask-WTF форми блюпринта products."""

from decimal import Decimal

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileSize
from wtforms import DecimalField, IntegerField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, InputRequired, Length, NumberRange, ValidationError

CATEGORIES = [
    ("computers", "Комп'ютери"),
    ("phones", "Смартфони"),
    ("accessories", "Аксесуари"),
    ("home", "Дім і побут"),
    ("other", "Інше"),
]
CATEGORY_LABELS = dict(CATEGORIES)

ALLOWED_IMAGE_EXTENSIONS = ["png", "jpg", "jpeg"]
MAX_IMAGE_SIZE = 2 * 1024 * 1024  # 2 МБ


def _strip(value):
    return value.strip() if isinstance(value, str) else value


def max_two_decimals(form, field):
    """Ціна — не більше двох знаків після коми."""
    if field.data is not None and field.data.as_tuple().exponent < -2:
        raise ValidationError("Ціна може мати не більше двох знаків після коми.")


class ProductForm(FlaskForm):
    name = StringField(
        "Назва",
        filters=[_strip],
        validators=[
            DataRequired(message="Вкажіть назву товару."),
            Length(min=3, max=100, message="Назва має містити від 3 до 100 символів."),
        ],
    )
    content = TextAreaField(
        "Опис",
        filters=[_strip],
        validators=[DataRequired(message="Додайте опис товару.")],
        render_kw={"rows": 5, "cols": 40},
    )
    price = DecimalField(
        "Ціна, $",
        places=2,
        validators=[
            InputRequired(message="Вкажіть ціну."),
            NumberRange(min=Decimal("0.01"), message="Ціна має бути додатною."),
            max_two_decimals,
        ],
        render_kw={"step": "0.01"},
    )
    category = SelectField("Категорія", choices=CATEGORIES)
    quantity = IntegerField(
        "Кількість",
        validators=[
            InputRequired(message="Вкажіть кількість."),
            NumberRange(min=0, message="Кількість не може бути від'ємною."),
        ],
        render_kw={"min": 0},
    )
    image = FileField(
        "Зображення",
        validators=[
            FileAllowed(ALLOWED_IMAGE_EXTENSIONS, message="Дозволені формати: PNG, JPG, JPEG."),
            FileSize(max_size=MAX_IMAGE_SIZE, message="Файл завеликий (максимум 2 МБ)."),
        ],
        render_kw={"accept": ".png,.jpg,.jpeg"},
    )
    submit = SubmitField("Зберегти")


class DeleteForm(FlaskForm):
    """Порожня форма: потрібна лише для CSRF-токена при видаленні."""
