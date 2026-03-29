import json
import os


def get_vendor(vendor_name):
    current_dir = os.path.dirname(__file__)
    file_path = os.path.join(current_dir, "vendors.json")

    with open(file_path, "r") as f:
        vendors_dict = json.load(f)

    return vendors_dict.get(vendor_name) or None
