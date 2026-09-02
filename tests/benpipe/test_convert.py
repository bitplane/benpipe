import pytest

from benpipe.convert import (
    BYTES_TAG,
    DICT_TAG,
    TUPLE_TAG,
    bytes_to_str,
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
    original = {b"binary": b"\xff\xfe\xfd", b"\xff": b"value"}

    assert to_bencode_types(to_json_types(original)) == original


def test_base64_prefix_is_ordinary_text():
    value = "__base64:aGVsbG8="

    assert to_bencode_types(value) == value.encode()


def test_invalid_tagged_binary_is_rejected():
    with pytest.raises(ValueError, match="Invalid base64"):
        to_bencode_types({BYTES_TAG: "not valid!"})


def test_bencode_dictionary_matching_a_tag_is_escaped():
    original = {BYTES_TAG.encode(): b"ordinary data"}

    assert to_bencode_types(to_json_types(original)) == original


def test_to_bencode_types_with_simple_data():
    assert to_bencode_types({"key": "value"}) == {b"key": b"value"}


def test_tuple_to_json():
    input_tuple = (123, b"\x01\x02\x03")

    json_data = to_json_types({"tuple": input_tuple})

    assert json_data == {"tuple": {TUPLE_TAG: [123, "\x01\x02\x03"]}}


def test_json_to_tuple():
    json_data = {"tuple": {TUPLE_TAG: [123, {BYTES_TAG: "AgM="}]}}

    bencode_data = to_bencode_types(json_data)

    assert bencode_data == {b"tuple": (123, b"\x02\x03")}


def test_dictionary_containing_old_tuple_key_stays_a_dictionary():
    value = {"__tuple": "hello", "other": 1}

    assert to_bencode_types(value) == {b"__tuple": b"hello", b"other": 1}


def test_bencode_dictionary_matching_tuple_tag_is_escaped():
    original = {TUPLE_TAG.encode(): [b"ordinary data"]}

    assert to_bencode_types(to_json_types(original)) == original


def test_invalid_tuple_tag_is_rejected():
    with pytest.raises(TypeError, match="must contain a list"):
        to_bencode_types({TUPLE_TAG: "not a list"})
