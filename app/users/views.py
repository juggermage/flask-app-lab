import re
from flask_login import login_user, logout_user, current_user, login_required
from sqlalchemy.exc import IntegrityError
from app import db
from .models import User
from .forms import RegistrationForm, LoginForm, LogoutForm

from flask import (
    flash,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from . import user_bp

THEMES = ("light", "dark")
THEME_COOKIE = "theme"
COOKIE_KEY_RE = re.compile(r"^[A-Za-z0-9_.\-]{1,64}$")  # дозволені символи ключа кукі


@user_bp.app_context_processor
def logout_form_context():
    return {"logout_form": LogoutForm()}


# login / profile / logout
@user_bp.route("/hi/<string:name>")  # /users/hi/ivan?age=45
def greetings(name):
    name = name.upper()
    age = request.args.get("age", None, int)

    return render_template("hi.html", name=name, age=age)


@user_bp.route("/admin")
def admin():
    """Приклад редіректу: перенаправляє на greetings для administrator."""
    to_url = url_for("users.greetings", name="administrator", age=45, _external=True)
    return redirect(to_url)


@user_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("users.account"))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Користувач з таким іменем або email вже існує.", "danger")
        else:
            flash("Реєстрація успішна! Тепер увійдіть у систему.", "success")
            return redirect(url_for("users.login"))
    return render_template("register.html", form=form, title="Реєстрація")


@user_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("users.account"))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(db.select(User).where(User.username == form.username.data))
        if user and user.check_password(form.password.data):
            if not user.password.startswith(("$2a$", "$2b$", "$2y$")):
                user.set_password(form.password.data)
                db.session.commit()
            login_user(user, remember=form.remember.data)
            flash(f"Ви успішно увійшли як {user.username}!", "success")
            return redirect(url_for("users.account"))
        flash("Wrong data! Try again!", "danger")
    return render_template("login.html", form=form, title="Вхід")


@user_bp.route("/account")
@login_required
def account():
    theme = request.cookies.get(THEME_COOKIE, "light")
    if theme not in THEMES:
        theme = "light"
    return render_template("account.html", title="Профіль", username=current_user.username,
                           user=current_user, theme=theme,
                           cookies=[(k, v) for k, v in request.cookies.items() if k not in ("session", "remember_token")])


@user_bp.route("/profile")
@login_required
def profile():
    return account()


@user_bp.route("/list")
@login_required
def users_list():
    users = db.session.scalars(db.select(User).order_by(User.id)).all()
    return render_template("users_list.html", users=users, title="Користувачі")


@user_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    if not LogoutForm().validate_on_submit():
        from flask import abort
        abort(400)
    logout_user()
    session.pop("user", None)
    flash("Ви вийшли з системи.", "info")
    return redirect(url_for("users.login"))


# Керування кукі

@user_bp.route("/cookies/add", methods=["POST"])
@login_required
def add_cookie():
    key = request.form.get("key", "").strip()
    value = request.form.get("value", "")
    max_age_raw = request.form.get("max_age", "").strip()

    if not COOKIE_KEY_RE.match(key):
        flash("Ключ кукі може містити лише латинські літери, цифри, '_', '-', '.' (до 64 символів).", "danger")
        return redirect(url_for("users.profile"))
    if key in ("session", "remember_token"):
        flash("Кукі 'session' службова — її змінювати не можна.", "danger")
        return redirect(url_for("users.profile"))

    max_age = None  # None - кукі діє до закриття браузера
    if max_age_raw:
        if not max_age_raw.isdigit() or int(max_age_raw) <= 0:
            flash("Термін дії має бути додатним цілим числом секунд.", "danger")
            return redirect(url_for("users.profile"))
        max_age = int(max_age_raw)

    response = make_response(redirect(url_for("users.profile")))
    response.set_cookie(key, value, max_age=max_age)
    term = f"{max_age} с" if max_age else "до закриття браузера"
    flash(f"Кукі '{key}' додано (термін дії: {term}).", "success")
    return response


@user_bp.route("/cookies/delete", methods=["POST"])
@login_required
def delete_cookie():
    key = request.form.get("key", "").strip()

    if key in ("session", "remember_token"):
        flash("Кукі 'session' видаляти не можна — вона зберігає ваш вхід. Скористайтесь кнопкою «Вийти».", "warning")
        return redirect(url_for("users.profile"))
    if key not in request.cookies:
        flash(f"Кукі з ключем '{key}' не знайдено.", "warning")
        return redirect(url_for("users.profile"))

    response = make_response(redirect(url_for("users.profile")))
    response.delete_cookie(key)
    flash(f"Кукі '{key}' видалено.", "success")
    return response


@user_bp.route("/cookies/delete-all", methods=["POST"])
@login_required
def delete_all_cookies():
    response = make_response(redirect(url_for("users.profile")))
    deleted = 0
    for key in request.cookies:
        if key in ("session", "remember_token"):  # лишаємо сесію, щоб користувача не "вибило"
            continue
        response.delete_cookie(key)
        deleted += 1
    flash(f"Видалено кукі: {deleted} (службову 'session' залишено).", "success")
    return response



# Вибір кольорової схеми

@user_bp.route("/theme/<string:scheme>")
@login_required
def set_theme(scheme):
    if scheme not in THEMES:
        flash("Невідома кольорова схема.", "danger")
        return redirect(url_for("users.profile"))

    response = make_response(redirect(url_for("users.profile")))
    # зберігаємо на рік, щоб вибір пам'ятався при наступних відвідуваннях
    response.set_cookie(THEME_COOKIE, scheme, max_age=60 * 60 * 24 * 365)
    flash("Кольорову схему змінено на {}.".format("темну" if scheme == "dark" else "світлу"), "success")
    return response
