import base64


def bytes_to_str(b: bytes) -> str:
    try:
        return b.decode("utf-8")
    except UnicodeDecodeError:
        return f"__base64:{base64.b64encode(b).decode()}"


def str_to_bytes(s: str) -> bytes:
    if s.startswith("__base64:"):
        return base64.b64decode(s[9:])
    else:
        return s.encode("utf-8")


def to_json_types(obj):
    """
    Use {"__tuple": []} for tuples
    Write binary data as base64 if it isn't UTF8.
    """
    if isinstance(obj, tuple):
        return {"__tuple": list(to_json_types(o) for o in obj)}
    if isinstance(obj, list):
        return [to_json_types(o) for o in obj]
    if isinstance(obj, bytes):
        return bytes_to_str(obj)
    if isinstance(obj, dict):
        return {to_json_types(key): to_json_types(value) for key, value in obj.items()}
    return obj


def to_bencode_types(obj):
    if isinstance(obj, dict):
        if "__tuple" in obj:
            return tuple(to_bencode_types(o) for o in obj["__tuple"])
        return {to_bencode_types(key): to_bencode_types(value) for key, value in obj.items()}
    if isinstance(obj, list):
        return [to_bencode_types(o) for o in obj]
    if isinstance(obj, str):
        return str_to_bytes(obj)

    return obj
