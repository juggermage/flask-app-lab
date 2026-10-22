from flask import render_template, request, redirect, url_for

from . import user_bp


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
