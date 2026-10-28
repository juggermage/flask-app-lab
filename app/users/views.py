import re
from functools import wraps

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

# Заглушка замість бази даних
USERS = {
    "user1": "12345",
    "admin": "admin",
}

THEMES = ("light", "dark")
THEME_COOKIE = "theme"
COOKIE_KEY_RE = re.compile(r"^[A-Za-z0-9_.\-]{1,64}$")  # дозволені символи ключа кукі


def login_required(view):
    """Пускає далі лише якщо користувач є в сесії, інакше -> login + flash."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user" not in session:
            flash("Спочатку увійдіть у систему, щоб переглянути профіль.", "danger")
            return redirect(url_for("users.login"))
        return view(*args, **kwargs)

    return wrapped



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


@user_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if username in USERS and USERS[username] == password:
            session["user"] = username  # зберігаємо користувача в сесію
            flash(f"Ви успішно увійшли як {username}!", "success")
            return redirect(url_for("users.profile"))

        flash("Wrong data! Try again!", "danger")
        return redirect(url_for("users.login"))

    return render_template("login.html", title="Вхід")


@user_bp.route("/profile")
@login_required
def profile():
    theme = request.cookies.get(THEME_COOKIE, "light")
    if theme not in THEMES:
        theme = "light"
    return render_template(
        "profile.html",
        title="Профіль",
        username=session["user"],
        theme=theme,
        cookies=request.cookies.items(),  # (ключ, значення) усіх кукі запиту
    )


@user_bp.route("/logout", methods=["POST"])
@login_required
def logout():
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
    if key == "session":
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

    if key == "session":
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
        if key == "session":  # лишаємо сесію, щоб користувача не "вибило"
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
