"""Flask-WTF форми застосунку (контактна форма)."""

from flask_wtf import FlaskForm
from wtforms import EmailField, SelectField, StringField, SubmitField, TelField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, Optional, Regexp

SUBJECT_CHOICES = [
    ("question", "Загальне питання"),
    ("cooperation", "Співпраця"),
    ("bug", "Повідомлення про помилку"),
    ("other", "Інше"),
]


def _strip(value):
    return value.strip() if isinstance(value, str) else value


class ContactForm(FlaskForm):
    name = StringField(
        "Ім'я",
        filters=[_strip],
        validators=[
            DataRequired(message="Вкажіть ім'я."),
            Length(min=4, max=10, message="Ім'я має містити від 4 до 10 символів."),
        ],
    )
    email = EmailField(
        "Email",
        filters=[_strip],
        validators=[
            DataRequired(message="Вкажіть email."),
            Email(message="Невірний формат email."),
        ],
    )
    phone = TelField(
        "Телефон",
        filters=[_strip],
        validators=[
            Optional(),
            Regexp(r"^\+380\d{9}$", message="Формат телефону: +380XXXXXXXXX (9 цифр після +380)."),
        ],
        render_kw={"placeholder": "+380XXXXXXXXX"},
    )
    subject = SelectField("Тема", choices=SUBJECT_CHOICES)
    message = TextAreaField(
        "Повідомлення",
        filters=[_strip],
        validators=[
            DataRequired(message="Введіть повідомлення."),
            Length(max=500, message="Повідомлення має бути не довшим за 500 символів."),
        ],
        render_kw={"rows": 5},
    )
    submit = SubmitField("Надіслати")
