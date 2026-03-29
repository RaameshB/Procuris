from .hello import hello_bp
from .users import users_bp
from .vendors import vendors_bp


def register_routes(app):
    app.register_blueprint(users_bp)
    app.register_blueprint(vendors_bp)
    app.register_blueprint(hello_bp)
