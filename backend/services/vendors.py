import json


def get_vendor(vendor_name):
    with open("vendors.json", "r") as f:
        vendors_dict = json.load(f)

    return vendors_dict.get(vendor_name) or None


print(get_vendor("tsm"))
