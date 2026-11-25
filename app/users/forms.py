from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Regexp, ValidationError
from app import db
from .models import User


def password_bytes(form, field):
    if len(field.data.encode("utf-8")) > 72:
        raise ValidationError("Пароль має містити не більше 72 байтів.")


class RegistrationForm(FlaskForm):
    username = StringField("Ім’я користувача", validators=[DataRequired(), Length(min=4, max=16), Regexp(r"^[A-Za-z][A-Za-z0-9_.]*$", message="Ім’я має починатися з літери та містити лише латинські літери, цифри, крапки або підкреслення.")])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)], filters=[lambda x: x.strip().lower() if x else x])
    password = PasswordField("Пароль", validators=[DataRequired(), Length(min=6), password_bytes])
    confirm_password = PasswordField("Підтвердження пароля", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Зареєструватися")

    def validate_username(self, field):
        if db.session.scalar(db.select(User).where(User.username == field.data)):
            raise ValidationError("Користувач з таким іменем вже існує.")

    def validate_email(self, field):
        if db.session.scalar(db.select(User).where(User.email == field.data)):
            raise ValidationError("Користувач з таким email вже існує.")


class LoginForm(FlaskForm):
    username = StringField("Ім’я користувача", validators=[DataRequired()])
    password = PasswordField("Пароль", validators=[DataRequired(), password_bytes])
    remember = BooleanField("Запам’ятати мене")
    submit = SubmitField("Увійти")


class LogoutForm(FlaskForm):
    pass
