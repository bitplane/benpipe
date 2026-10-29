"""JSON helpers that preserve bencode's arbitrary-precision integers."""

import json

from ._bencode import _encode_integer, _parse_integer


def parse_integer(token):
    """Parse a JSON integer without the interpreter's decimal string limit."""
    return _parse_integer(token.encode("ascii"), 0, strict=False)


def dumps(value):
    """Serialize converted values with four-space indentation.

    Callers must validate nesting first. Strings use the standard JSON encoder;
    integers use the same decimal conversion as the bencode codec. No global
    interpreter limits are changed.
    """
    return "".join(_parts(value, 0))


def _parts(value, depth):
    if type(value) is int:
        yield _encode_integer(value).decode("ascii")
    elif isinstance(value, str):
        yield json.dumps(value)
    elif isinstance(value, (list, dict)):
        is_dict = isinstance(value, dict)
        opening, closing = ("{", "}") if is_dict else ("[", "]")
        yield opening
        if value:
            children = value.items() if is_dict else enumerate(value)
            for index, (key, child) in enumerate(children):
                yield ",\n" if index else "\n"
                yield "    " * (depth + 1)
                if is_dict:
                    yield json.dumps(key)
                    yield ": "
                yield from _parts(child, depth + 1)
            yield "\n" + "    " * depth
        yield closing
    else:
        raise TypeError(f"Unsupported JSON value: {type(value).__name__}")
