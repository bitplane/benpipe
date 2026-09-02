import base64
import binascii
from dataclasses import dataclass

from ._bencode import BencodeDict

BYTES_TAG = "__benpipe_bytes__"
DICT_TAG = "__benpipe_dict__"
LEGACY_TUPLE_TAG = "__benpipe_tuple__"


@dataclass(frozen=True, slots=True)
class JsonObject:
    entries: tuple[tuple[str, object], ...]


def json_object(entries: list[tuple[str, object]]) -> JsonObject:
    return JsonObject(tuple(entries))


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
    return len(obj) == 1 and next(iter(obj)) in {BYTES_TAG, DICT_TAG, LEGACY_TUPLE_TAG}


def to_json_types(obj):
    """
    Represent binary data and non-JSON dictionaries with typed JSON objects.
    """
    if isinstance(obj, list):
        return [to_json_types(o) for o in obj]
    if isinstance(obj, bytes):
        return binary_to_json(obj)
    if isinstance(obj, (dict, BencodeDict)):
        source_items = obj.items() if isinstance(obj, dict) else obj.entries
        items = [[to_json_types(key), to_json_types(value)] for key, value in source_items]
        keys = [key for key, _ in items]
        if any(not isinstance(key, str) for key in keys) or len(set(keys)) != len(keys):
            return {DICT_TAG: items}
        converted = dict(items)
        if is_tagged_object(converted):
            return {DICT_TAG: items}
        return converted
    return obj


def _object_to_bencode(entries):
    if len(entries) == 1:
        tag, tagged_value = entries[0]
        if tag == BYTES_TAG:
            return binary_from_json({BYTES_TAG: tagged_value})
        if tag == DICT_TAG:
            items = tagged_value
            if not isinstance(items, list) or any(not isinstance(item, list) or len(item) != 2 for item in items):
                raise ValueError(f"{DICT_TAG} must contain key-value pairs")
            return BencodeDict(tuple((to_bencode_types(key), to_bencode_types(value)) for key, value in items))
        if tag == LEGACY_TUPLE_TAG:
            raise ValueError(f"{LEGACY_TUPLE_TAG} is no longer supported; use a JSON list")
    return BencodeDict(tuple((str_to_bytes(key), to_bencode_types(value)) for key, value in entries))


def to_bencode_types(obj):
    if isinstance(obj, JsonObject):
        return _object_to_bencode(obj.entries)
    if isinstance(obj, dict):
        return _object_to_bencode(tuple(obj.items()))
    if isinstance(obj, list):
        return [to_bencode_types(o) for o in obj]
    if isinstance(obj, str):
        return str_to_bytes(obj)

    return obj
