from flask import Blueprint, jsonify

vendors_bp = Blueprint("vendors_bp", __name__, url_prefix="/api/vendors")


@vendors_bp.get("/overview/<vendor_name>")
def get_overview(vendor_name):
    response_data = {
        "status": "success",
        "data": {},
        "message": f"Overview for {vendor_name}",
    }
    return jsonify(response_data), 200
