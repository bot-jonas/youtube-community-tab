import base64


def dict_to_message(d, msg):
    for k, v in d.items():
        if isinstance(v, dict):
            dict_to_message(v, getattr(msg, k))
        else:
            setattr(msg, k, v)


def message_to_dict(msg):
    out = {}
    for field in msg.DESCRIPTOR.fields:
        value = getattr(msg, field.name)
        if field.type == field.TYPE_MESSAGE:
            out[field.name] = message_to_dict(value)
        else:
            out[field.name] = value
    return out


def message_from_json(data, klass):
    msg = klass()
    dict_to_message(data, msg)

    return msg


def message_from_key(key, klass):
    msg = klass()
    msg.ParseFromString(base64.b64decode(key))

    return msg


def message_from_key_urlsafe(key, klass):
    msg = klass()
    msg.ParseFromString(base64.urlsafe_b64decode(key.replace("%3D", "=")))

    return msg


def message_to_key(msg):
    return base64.b64encode(msg.SerializeToString()).decode()


def message_to_key_urlsafe(msg):
    return base64.urlsafe_b64encode(msg.SerializeToString()).decode().replace("=", "%3D")
