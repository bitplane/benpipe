"""Small, strict-output bencode codec."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias


class DecodeError(ValueError):
    """Raised when bencoded input cannot be decoded."""

    def __init__(self, message: str, offset: int):
        super().__init__(f"{message} at byte {offset}")
        self.offset = offset


class EncodeError(TypeError):
    """Raised when a Python value cannot be bencoded."""


@dataclass(frozen=True, slots=True)
class BencodeDict:
    """An ordered bencode dictionary that can preserve duplicate keys."""

    entries: tuple[tuple[bytes, BencodeValue], ...]


BencodeValue: TypeAlias = int | bytes | list["BencodeValue"] | BencodeDict


@dataclass(slots=True)
class _Frame:
    kind: str
    values: list
    offset: int
    pending_key: bytes | None = None
    last_key: bytes | None = None


def _parse_integer(token: bytes, offset: int, strict: bool) -> int:
    if not token:
        raise DecodeError("Empty integer", offset)

    negative = token[:1] == b"-"
    positive = token[:1] == b"+"
    digits = token[1:] if negative or positive else token
    if not digits or any(digit < 48 or digit > 57 for digit in digits):
        raise DecodeError("Invalid integer", offset)
    if strict:
        if positive:
            raise DecodeError("A canonical integer cannot have a plus sign", offset)
        if len(digits) > 1 and digits[0] == 48:
            raise DecodeError("A canonical integer cannot have a leading zero", offset)
        if negative and digits == b"0":
            raise DecodeError("Negative zero is not canonical", offset)

    value = 0
    for digit in digits:
        value = value * 10 + digit - 48
    return -value if negative else value


def _parse_length(data: bytes, start: int, colon: int, strict: bool) -> int:
    digits = data[start:colon]
    if not digits or any(digit < 48 or digit > 57 for digit in digits):
        raise DecodeError("Invalid byte string length", start)
    if strict and len(digits) > 1 and digits[0] == 48:
        raise DecodeError("A canonical byte string length cannot have a leading zero", start)

    remaining = len(data) - colon - 1
    length = 0
    for digit in digits:
        length = length * 10 + digit - 48
        if length > remaining:
            raise DecodeError("Byte string extends beyond the input", start)
    return length


def decode(data: bytes, *, strict: bool = False) -> BencodeValue:
    """Decode one complete bencode value.

    Lenient mode accepts recoverable non-canonical spelling and dictionary
    order. Strict mode additionally enforces canonical spelling and key order.
    """
    if type(data) is not bytes:
        raise TypeError("bencode input must be bytes")
    if not data:
        raise DecodeError("Expected a bencode value", 0)

    frames: list[_Frame] = []
    index = 0
    value: BencodeValue | None = None

    while True:
        if value is None:
            if index >= len(data):
                offset = frames[-1].offset if frames else index
                raise DecodeError("Unterminated container", offset)

            token = data[index]
            if token == 105:  # i
                end = data.find(b"e", index + 1)
                if end < 0:
                    raise DecodeError("Unterminated integer", index)
                value = _parse_integer(data[index + 1 : end], index, strict)
                index = end + 1
            elif 48 <= token <= 57:
                colon = data.find(b":", index + 1)
                if colon < 0:
                    raise DecodeError("Unterminated byte string length", index)
                length = _parse_length(data, index, colon, strict)
                start = colon + 1
                value = data[start : start + length]
                index = start + length
            elif token == 108:  # l
                frames.append(_Frame("list", [], index))
                index += 1
                continue
            elif token == 100:  # d
                frames.append(_Frame("dict", [], index))
                index += 1
                continue
            elif token == 101:  # e
                if not frames:
                    raise DecodeError("Unexpected container terminator", index)
                frame = frames.pop()
                if frame.kind == "dict" and frame.pending_key is not None:
                    raise DecodeError("Dictionary key has no value", index)
                index += 1
                value = frame.values if frame.kind == "list" else BencodeDict(tuple(frame.values))
            else:
                raise DecodeError("Invalid bencode token", index)

        if not frames:
            if index != len(data):
                raise DecodeError("Trailing data", index)
            return value

        frame = frames[-1]
        if frame.kind == "list":
            frame.values.append(value)
        elif frame.pending_key is None:
            if type(value) is not bytes:
                raise DecodeError("Dictionary keys must be byte strings", index)
            if strict and frame.last_key is not None and value < frame.last_key:
                raise DecodeError("Dictionary keys are not sorted", index)
            frame.pending_key = value
            frame.last_key = value
        else:
            frame.values.append((frame.pending_key, value))
            frame.pending_key = None
        value = None


def _encode_integer(value: int) -> bytes:
    if value == 0:
        return b"0"

    negative = value < 0
    value = abs(value)
    chunks: list[int] = []
    while value:
        value, chunk = divmod(value, 1_000_000_000)
        chunks.append(chunk)

    result = str(chunks.pop()).encode("ascii")
    while chunks:
        result += f"{chunks.pop():09d}".encode("ascii")
    return b"-" + result if negative else result


def encode(value: BencodeValue | dict[bytes, BencodeValue]) -> bytes:
    """Encode a Python value as canonical bencode."""
    output: list[bytes] = []
    active_containers: set[int] = set()
    actions: list[tuple[str, object, str]] = [("value", value, "$")]

    while actions:
        action, current, path = actions.pop()
        if action == "token":
            output.append(current)
            continue
        if action == "leave":
            active_containers.remove(current)
            continue

        current_type = type(current)
        if current_type is bytes:
            output.extend((str(len(current)).encode("ascii"), b":", current))
        elif current_type is int:
            output.extend((b"i", _encode_integer(current), b"e"))
        elif current_type is list:
            container_id = id(current)
            if container_id in active_containers:
                raise EncodeError(f"Cyclic container at {path}")
            active_containers.add(container_id)
            actions.append(("leave", container_id, path))
            actions.append(("token", b"e", path))
            for item_index in range(len(current) - 1, -1, -1):
                actions.append(("value", current[item_index], f"{path}[{item_index}]"))
            actions.append(("token", b"l", path))
        elif current_type is dict or current_type is BencodeDict:
            container_id = id(current)
            if container_id in active_containers:
                raise EncodeError(f"Cyclic container at {path}")
            active_containers.add(container_id)
            entries = list(current.items()) if current_type is dict else list(current.entries)
            for key, _ in entries:
                if type(key) is not bytes:
                    raise EncodeError(f"Dictionary key at {path} must be bytes")
            entries.sort(key=lambda item: item[0])

            actions.append(("leave", container_id, path))
            actions.append(("token", b"e", path))
            for item_index in range(len(entries) - 1, -1, -1):
                key, item = entries[item_index]
                actions.append(("value", item, f"{path}[{key!r}]"))
                actions.append(("value", key, f"{path}.key[{item_index}]"))
            actions.append(("token", b"d", path))
        else:
            raise EncodeError(f"Unsupported value of type {current_type.__name__} at {path}")

    return b"".join(output)
