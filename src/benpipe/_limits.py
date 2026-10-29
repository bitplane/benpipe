"""Bound nesting at the JSON conversion boundary, before recursive work."""

from ._bencode import BencodeDict
from .convert import JsonObject

MAX_NESTING = 100


def _check_depth(depth):
    if depth > MAX_NESTING:
        raise ValueError(f"Maximum nesting depth of {MAX_NESTING} exceeded")


def check_json_nesting(text):
    """Check container depth without parsing strings or recursing."""
    depth = 0
    in_string = False
    escaped = False
    for char in text:
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
        elif char == '"':
            in_string = True
        elif char in "[{":
            depth += 1
            _check_depth(depth)
        elif char in "]}":
            depth -= 1


def check_value_nesting(value):
    """Check container depth using a stack before type conversion/serialization."""
    pending = [(value, 0)]
    while pending:
        current, depth = pending.pop()
        if isinstance(current, (BencodeDict, JsonObject)):
            children = (value for _, value in current.entries)
        elif isinstance(current, dict):
            children = current.values()
        elif isinstance(current, list):
            children = current
        else:
            continue
        depth += 1
        _check_depth(depth)
        pending.extend((child, depth) for child in children)
