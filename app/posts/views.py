from flask import abort, flash, redirect, render_template, request, session, url_for

from app import db

from . import post_bp
from .forms import CATEGORY_LABELS, DeleteForm, PostForm
from .models import Post


@post_bp.app_template_filter("post_category")
def post_category(key):
    return CATEGORY_LABELS.get(key, key)


def _get_or_404(post_id):
    return db.get_or_404(Post, post_id)


@post_bp.route("")
def all_posts():
    """Список усіх видимих (активних) постів за датою публікації (спадання)."""
    stmt = db.select(Post).where(Post.is_active.is_(True)).order_by(Post.posted.desc(), Post.id.desc())
    posts = db.session.scalars(stmt).all()
    return render_template("posts.html", title="Пости", posts=posts)


@post_bp.route("/<int:id>")
def detail_post(id):
    post = _get_or_404(id)
    return render_template("detail_post.html", title=post.title, post=post)


@post_bp.route("/create", methods=["GET", "POST"])
def add_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(
            title=form.title.data,
            content=form.content.data,
            is_active=form.is_active.data,
            posted=form.publish_date.data,
            category=form.category.data,
            # автор — користувач із сесії, інакше Anonymous (поле author обмежене 20 символами)
            author=session.get("user", "Anonymous")[:20],
        )
        db.session.add(post)
        db.session.commit()
        flash(f"Пост «{post.title}» успішно додано.", "success")
        return redirect(url_for("posts.all_posts"))  # PRG

    if request.method == "POST":
        flash("Пост не збережено: перевірте виділені поля.", "danger")
    return render_template("add_post.html", title="Новий пост", form=form, post=None)


@post_bp.route("/<int:id>/update", methods=["GET", "POST"])
def update_post(id):
    post = _get_or_404(id)
    form = PostForm(obj=post)  # title, content, is_active, category заповнюються автоматично
    if request.method == "GET":
        # назви publish_date (форма) і posted (модель) різні — підставляємо вручну
        form.publish_date.data = post.posted

    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        post.is_active = form.is_active.data
        post.category = form.category.data
        post.posted = form.publish_date.data
        db.session.commit()
        flash(f"Пост «{post.title}» оновлено.", "success")
        return redirect(url_for("posts.detail_post", id=post.id))  # PRG

    if request.method == "POST":
        flash("Зміни не збережено: перевірте виділені поля.", "danger")
    return render_template("add_post.html", title="Редагувати пост", form=form, post=post)


@post_bp.route("/<int:id>/delete", methods=["GET", "POST"])
def delete_post(id):
    """GET — сторінка підтвердження, POST — фактичне видалення."""
    post = _get_or_404(id)
    form = DeleteForm()
    if request.method == "POST":
        if not form.validate_on_submit():
            flash("Не вдалося видалити пост (недійсний CSRF-токен).", "danger")
            return redirect(url_for("posts.detail_post", id=id))
        title = post.title
        db.session.delete(post)
        db.session.commit()
        flash(f"Пост «{title}» успішно видалено.", "danger")
        return redirect(url_for("posts.all_posts"))
    return render_template("delete_confirm.html", title="Видалення поста", post=post, form=form)
