from flask import Blueprint

user_bp = Blueprint(
    "users",
    __name__,
    url_prefix="/users",
    template_folder="templates/users",
)

from . import models, views  # noqa: E402,F401  (models — щоб Alembic бачив таблицю users)
