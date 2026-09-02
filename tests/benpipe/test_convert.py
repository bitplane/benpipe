import pytest

from benpipe._bencode import BencodeDict
from benpipe.convert import (
    BYTES_TAG,
    DICT_TAG,
    LEGACY_TUPLE_TAG,
    bytes_to_str,
    json_object,
    str_to_bytes,
    to_bencode_types,
    to_json_types,
)


def test_bytes_to_str_utf8():
    assert bytes_to_str(b"hello") == "hello"


def test_bytes_to_str_non_utf8():
    with pytest.raises(UnicodeDecodeError):
        bytes_to_str(b"\xff\xfe\xfd")


def test_str_to_bytes_utf8():
    assert str_to_bytes("hello") == b"hello"


def test_str_to_bytes_base64():
    assert str_to_bytes("__base64://79") == b"__base64://79"


def test_to_json_types_with_simple_data():
    assert to_json_types({"key": b"hello"}) == {"key": "hello"}


def test_to_json_types_with_binary_data():
    input_data = {b"\xff\xfe\xfd": b"\xfa\xfb\xfc"}
    expected_output = {
        DICT_TAG: [
            [
                {BYTES_TAG: "//79"},
                {BYTES_TAG: "+vv8"},
            ]
        ]
    }

    assert to_json_types(input_data) == expected_output


def test_binary_data_round_trip():
    original = BencodeDict(((b"binary", b"\xff\xfe\xfd"), (b"\xff", b"value")))

    assert to_bencode_types(to_json_types(original)) == original


def test_base64_prefix_is_ordinary_text():
    value = "__base64:aGVsbG8="

    assert to_bencode_types(value) == value.encode()


def test_invalid_tagged_binary_is_rejected():
    with pytest.raises(ValueError, match="Invalid base64"):
        to_bencode_types({BYTES_TAG: "not valid!"})


def test_tagged_binary_requires_a_string():
    with pytest.raises(TypeError, match="base64 string"):
        to_bencode_types({BYTES_TAG: 123})


def test_tagged_dictionary_requires_pairs():
    with pytest.raises(ValueError, match="key-value pairs"):
        to_bencode_types({DICT_TAG: ["not a pair"]})


def test_bencode_dictionary_matching_a_tag_is_escaped():
    original = BencodeDict(((BYTES_TAG.encode(), b"ordinary data"),))

    assert to_bencode_types(to_json_types(original)) == original


def test_to_bencode_types_with_simple_data():
    assert to_bencode_types({"key": "value"}) == BencodeDict(((b"key", b"value"),))


def test_json_object_preserves_duplicate_keys():
    obj = json_object([("key", 1), ("key", 2)])

    assert to_bencode_types(obj) == BencodeDict(((b"key", 1), (b"key", 2)))


def test_duplicate_bencode_keys_use_dictionary_tag():
    value = BencodeDict(((b"key", 1), (b"key", 2)))

    assert to_json_types(value) == {DICT_TAG: [["key", 1], ["key", 2]]}


def test_legacy_tuple_tag_is_rejected():
    with pytest.raises(ValueError, match="no longer supported"):
        to_bencode_types({LEGACY_TUPLE_TAG: [1, 2]})


def test_dictionary_containing_old_tuple_key_stays_a_dictionary():
    value = {"__tuple": "hello", "other": 1}

    assert to_bencode_types(value) == BencodeDict(((b"__tuple", b"hello"), (b"other", 1)))


def test_bencode_dictionary_matching_legacy_tuple_tag_is_escaped():
    original = BencodeDict(((LEGACY_TUPLE_TAG.encode(), [b"ordinary data"]),))

    assert to_bencode_types(to_json_types(original)) == original
