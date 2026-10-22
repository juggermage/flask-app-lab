from flask import Flask

app = Flask(__name__)
app.config.from_pyfile("../config.py")

from . import views  # noqa: E402,F401

from .users import user_bp  # noqa: E402
from .products import product_bp  # noqa: E402

app.register_blueprint(user_bp)
app.register_blueprint(product_bp)
