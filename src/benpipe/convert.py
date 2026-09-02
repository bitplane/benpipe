import base64
import binascii

BYTES_TAG = "__benpipe_bytes__"
DICT_TAG = "__benpipe_dict__"
TUPLE_TAG = "__benpipe_tuple__"


def bytes_to_str(b: bytes) -> str:
    return b.decode("utf-8")


def str_to_bytes(s: str) -> bytes:
    return s.encode("utf-8")


def binary_to_json(b: bytes) -> str | dict[str, str]:
    try:
        return bytes_to_str(b)
    except UnicodeDecodeError:
        return {BYTES_TAG: base64.b64encode(b).decode("ascii")}


def binary_from_json(obj: dict) -> bytes:
    encoded = obj[BYTES_TAG]
    if not isinstance(encoded, str):
        raise TypeError(f"{BYTES_TAG} must contain a base64 string")
    try:
        return base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as error:
        raise ValueError(f"Invalid base64 data in {BYTES_TAG}") from error


def is_tagged_object(obj: dict) -> bool:
    return len(obj) == 1 and next(iter(obj)) in {BYTES_TAG, DICT_TAG, TUPLE_TAG}


def to_json_types(obj):
    """
    Represent tuples and non-UTF-8 binary data with typed JSON objects.
    """
    if isinstance(obj, tuple):
        return {TUPLE_TAG: [to_json_types(o) for o in obj]}
    if isinstance(obj, list):
        return [to_json_types(o) for o in obj]
    if isinstance(obj, bytes):
        return binary_to_json(obj)
    if isinstance(obj, dict):
        items = [[to_json_types(key), to_json_types(value)] for key, value in obj.items()]
        if any(not isinstance(key, str) for key, _ in items):
            return {DICT_TAG: items}
        converted = dict(items)
        if is_tagged_object(converted):
            return {DICT_TAG: items}
        return converted
    return obj


def to_bencode_types(obj):
    if isinstance(obj, dict):
        if len(obj) == 1 and BYTES_TAG in obj:
            return binary_from_json(obj)
        if len(obj) == 1 and DICT_TAG in obj:
            items = obj[DICT_TAG]
            if not isinstance(items, list) or any(not isinstance(item, list) or len(item) != 2 for item in items):
                raise ValueError(f"{DICT_TAG} must contain key-value pairs")
            return {to_bencode_types(key): to_bencode_types(value) for key, value in items}
        if len(obj) == 1 and TUPLE_TAG in obj:
            items = obj[TUPLE_TAG]
            if not isinstance(items, list):
                raise TypeError(f"{TUPLE_TAG} must contain a list")
            return tuple(to_bencode_types(o) for o in items)
        return {to_bencode_types(key): to_bencode_types(value) for key, value in obj.items()}
    if isinstance(obj, list):
        return [to_bencode_types(o) for o in obj]
    if isinstance(obj, str):
        return str_to_bytes(obj)

    return obj
