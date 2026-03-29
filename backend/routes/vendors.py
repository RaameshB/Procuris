from flask import Blueprint, jsonify, request
from services.vendors import get_vendor

vendors_bp = Blueprint("vendors_bp", __name__, url_prefix="/api/vendors")


@vendors_bp.get("/")
def get_overview():
    print("hello")
    vendor_name = request.args.get("vendor_name")
    print("Vendor name:", vendor_name)
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
