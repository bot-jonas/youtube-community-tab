import json


def safely_get_value_from_key(*args, default=None):
    obj = args[0]
    keys = args[1:]

    for key in keys:
        try:
            obj = obj[key]
        except Exception:
            return default

    return obj


def save_object_to_file(obj, path):
    with open(path, "w") as f:
        f.write(json.dumps(obj, indent=4))
