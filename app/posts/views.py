from flask import flash, redirect, render_template, request, session, url_for
from sqlalchemy.orm import joinedload, selectinload

from app import db

from . import post_bp
from .forms import CATEGORY_LABELS, DeleteForm, PostForm
from .models import Post, Tag
from app.users.models import User


@post_bp.app_template_filter("post_category")
def post_category(key):
    return CATEGORY_LABELS.get(key, key)


def _get_or_404(post_id):
    return db.get_or_404(Post, post_id)


def _selected_tags(tag_ids):
    """Повертає об'єкти Tag за списком id (порожній список -> порожній результат)."""
    if not tag_ids:
        return []
    return db.session.scalars(db.select(Tag).where(Tag.id.in_(tag_ids))).all()


@post_bp.route("")
def all_posts():
    """Список усіх видимих (активних) постів за датою публікації (спадання)."""
    stmt = (
        db.select(Post)
        .where(Post.is_active.is_(True))
        .options(joinedload(Post.user), selectinload(Post.tags))  # без N+1 (лаб. 8, п. 13)
        .order_by(Post.posted.desc(), Post.id.desc())
    )
    posts = db.session.scalars(stmt).all()
    return render_template("posts.html", title="Пости", posts=posts)


@post_bp.route("/<int:id>")
def detail_post(id):
    post = _get_or_404(id)
    return render_template("detail_post.html", title=post.title, post=post)


@post_bp.route("/create", methods=["GET", "POST"])
def add_post():
    form = PostForm()
    if request.method == "GET":
        # якщо ім'я користувача із сесії є серед авторів у БД — обираємо його за замовчуванням
        current = db.session.scalar(db.select(User).where(User.username == session.get("user")))
        if current:
            form.author_id.data = current.id
    if not form.author_id.choices:
        flash("У БД ще немає авторів: спочатку додайте користувача (flask shell).", "warning")
    if form.validate_on_submit():
        post = Post(
            title=form.title.data,
            content=form.content.data,
            is_active=form.is_active.data,
            posted=form.publish_date.data,
            category=form.category.data,
            user_id=form.author_id.data,
            tags=_selected_tags(form.tags.data),
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
        form.author_id.data = post.user_id
        form.tags.data = [t.id for t in post.tags]

    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        post.is_active = form.is_active.data
        post.category = form.category.data
        post.posted = form.publish_date.data
        post.user_id = form.author_id.data
        post.tags = _selected_tags(form.tags.data)
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
