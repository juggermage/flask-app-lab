from flask import Blueprint

product_bp = Blueprint(
    "products",
    __name__,
    url_prefix="/product",
    template_folder="templates/products",
    static_folder="static",  # app/products/static/uploads/ -> /product/static/uploads/...
)

from . import views, models  # noqa: E402,F401
