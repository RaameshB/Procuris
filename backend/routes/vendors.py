from flask import Blueprint, jsonify
from services.vendors import get_vendor

vendors_bp = Blueprint("vendors_bp", __name__, url_prefix="/api/vendors")


@vendors_bp.get("/<vendor_name>")
def get_overview(vendor_name):
    vendor_data = get_vendor(vendor_name)

    if not vendor_data:
        return jsonify(
            {"status": "error", "data": None, "message": "Vendor not found"}
        ), 404

    response_data = {
        "status": "success",
        "data": vendor_data,
        "message": f"Overview for {vendor_name}",
    }
    return jsonify(response_data), 200
