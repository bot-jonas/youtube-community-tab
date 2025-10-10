import json
from functools import reduce


def deep_get(data, path, default=None):
    keys = path.split(".")
    try:
        return reduce(
            lambda d, key: (d[int(key)] if isinstance(d, list) and key.isdigit() else d.get(key) if isinstance(d, dict) else {}),
            keys,
            data,
        )
    except (KeyError, IndexError, TypeError, ValueError):
        return default


def deep_pop(data, path):
    path_ref, pop_key = path.rsplit(".", 1)
    ref = deep_get(data, path_ref)

    if pop_key in ref:
        ref.pop(pop_key)


def search_key(key, data, current_key=[]):
    found = []

    if type(data).__name__ == "dict":
        keys = list(data.keys())
    elif type(data).__name__ == "list":
        keys = list(range(len(data)))
    else:
        return []

    if key in keys:
        found.append((current_key + [key], data[key]))
        keys.remove(key)

    for k in keys:
        found += search_key(key, data[k], current_key=current_key + [k])

    return found


def save_object_to_file(obj, path):
    with open(path, "w") as f:
        f.write(json.dumps(obj, indent=4))
