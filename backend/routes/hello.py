from flask import Blueprint, jsonify

hello_bp = Blueprint("hello_bp", __name__, url_prefix="/api/hello-world")


@hello_bp.route("/")
def hello_world():
    return jsonify(
        {"message": "Hello, World!", "status": "ok", "data": "Hello, World!"}
    )
