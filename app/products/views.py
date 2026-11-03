import os
import uuid

from flask import abort, current_app, flash, redirect, render_template, request, url_for
from werkzeug.datastructures import FileStorage

from . import product_bp, storage
from .forms import CATEGORY_LABELS, DeleteForm, ProductForm


# ---------- допоміжні функції для зображень ----------

def save_image(file):
    """Зберігає файл під випадковим UUID-іменем. Повертає шлях відносно static/ блюпринта."""
    ext = file.filename.rsplit(".", 1)[-1].lower()  # розширення вже перевірив FileAllowed
    filename = f"{uuid.uuid4().hex}.{ext}"
    folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(folder, exist_ok=True)
    file.save(os.path.join(folder, filename))
    return f"uploads/{filename}"


def remove_image(rel_path):
    """Видаляє файл зображення, якщо він лежить у папці завантажень."""
    if not rel_path:
        return
    folder = os.path.abspath(current_app.config["UPLOAD_FOLDER"])
    path = os.path.abspath(os.path.join(folder, os.path.basename(rel_path)))
    if os.path.dirname(path) == folder and os.path.isfile(path):
        os.remove(path)


@product_bp.app_template_global()
def product_image_url(product):
    """URL зображення або None, якщо його немає (чи файл зник з диска)."""
    rel_path = product.get("image")
    if not rel_path:
        return None
    folder = os.path.abspath(current_app.config["UPLOAD_FOLDER"])
    if not os.path.isfile(os.path.join(folder, os.path.basename(rel_path))):
        return None
    return url_for("products.static", filename=rel_path)


@product_bp.app_template_filter("category_label")
def category_label(key):
    return CATEGORY_LABELS.get(key, key)


def _get_or_404(product_id):
    product = storage.get_product(product_id)
    if product is None:
        abort(404)
    return product


def _form_data(form):
    return {
        "name": form.name.data,
        "content": form.content.data,
        "price": float(form.price.data),
        "category": form.category.data,
        "quantity": form.quantity.data,
    }


def _uploaded(form):
    return form.image.data if isinstance(form.image.data, FileStorage) else None


# ---------- маршрути ----------

@product_bp.route("")
def product_list():
    """Список усіх товарів."""
    return render_template("products.html", title="Товари", products=storage.all_products())


@product_bp.route("/<int:product_id>")
def product_detail(product_id):
    """Детальна інформація про товар за його id."""
    product = _get_or_404(product_id)
    return render_template(
        "detail_product.html", title=product["name"], product=product, delete_form=DeleteForm()
    )


@product_bp.route("/add", methods=["GET", "POST"])
def product_add():
    form = ProductForm()
    if form.validate_on_submit():
        data = _form_data(form)
        upload = _uploaded(form)
        data["image"] = save_image(upload) if upload else None
        product = storage.add_product(data)
        flash(f"Товар «{product['name']}» успішно додано.", "success")
        return redirect(url_for("products.product_detail", product_id=product["id"]))  # PRG

    if request.method == "POST":
        flash("Товар не збережено: перевірте виділені поля.", "danger")
    return render_template("product_form.html", title="Додати товар", form=form, product=None)


@product_bp.route("/<int:product_id>/edit", methods=["GET", "POST"])
def product_edit(product_id):
    product = _get_or_404(product_id)
    # поточні дані підставляємо у форму (зображення — окремо, його не можна передзаповнити)
    form = ProductForm(data={k: v for k, v in product.items() if k != "image"})

    if form.validate_on_submit():
        data = _form_data(form)
        upload = _uploaded(form)
        old_image = product.get("image")
        if upload:
            data["image"] = save_image(upload)
        storage.update_product(product_id, data)
        if upload:
            remove_image(old_image)  # старий файл видаляємо лише після успішного збереження
        flash(f"Товар «{data['name']}» оновлено.", "success")
        return redirect(url_for("products.product_detail", product_id=product_id))  # PRG

    if request.method == "POST":
        flash("Зміни не збережено: перевірте виділені поля.", "danger")
    return render_template("product_form.html", title="Редагувати товар", form=form, product=product)


@product_bp.route("/<int:product_id>/delete", methods=["POST"])
def product_delete(product_id):
    product = _get_or_404(product_id)
    form = DeleteForm()
    if not form.validate_on_submit():
        flash("Не вдалося видалити товар (недійсний CSRF-токен).", "danger")
        return redirect(url_for("products.product_detail", product_id=product_id))

    storage.delete_product(product_id)
    remove_image(product.get("image"))
    flash(f"Товар «{product['name']}» видалено.", "success")
    return redirect(url_for("products.product_list"))
