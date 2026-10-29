import json
import sys

import pytest

from benpipe.benpipe import to_bencode, to_json
from benpipe.convert import DICT_TAG


@pytest.mark.parametrize(
    ("bencoded", "expected"),
    [
        (b"i1e", 1),
        (b"4:spam", "spam"),
        (b"li1ee", [1]),
        (b"d1:ai1ee", {"a": 1}),
    ],
)
def test_to_json_accepts_one_complete_value(bencoded, expected):
    assert json.loads(to_json(bencoded)) == expected


@pytest.mark.parametrize("suffix", [b"junk", b"i2e"])
def test_to_json_rejects_trailing_data(suffix):
    with pytest.raises(ValueError, match="Trailing data|exactly one"):
        to_json(b"d1:ai1ee" + suffix)


def test_to_bencode_encodes_json():
    assert to_bencode('{"spam": [1, "eggs"]}') == b"d4:spamli1e4:eggsee"


def test_to_bencode_preserves_duplicate_json_keys():
    assert to_bencode('{"key": 1, "key": 2}') == b"d3:keyi1e3:keyi2ee"


def test_to_json_preserves_duplicate_bencode_keys():
    converted = json.loads(to_json(b"d3:keyi1e3:keyi2ee"))

    assert converted == {DICT_TAG: [["key", 1], ["key", 2]]}


@pytest.mark.parametrize("invalid_json", ["not json", "1.5"])
def test_to_bencode_reports_invalid_input(invalid_json):
    with pytest.raises(ValueError, match="Error encoding JSON"):
        to_bencode(invalid_json)


def test_nesting_boundary_round_trip():
    data = b"l" * 100 + b"i1e" + b"e" * 100
    assert to_bencode(to_json(data)) == data


def test_nesting_check_ignores_escaped_strings():
    text = '[\\"' * 200
    assert to_bencode(json.dumps(text)) == str(len(text)).encode() + b":" + text.encode()


def test_tag_expansion_obeys_json_nesting_limit():
    data = b"l" * 99 + b"1:\xff" + b"e" * 99
    assert to_bencode(to_json(data)) == data
    with pytest.raises(ValueError, match="Maximum nesting"):
        to_json(b"l" + data + b"e")


@pytest.mark.parametrize("encoding", ["utf-8", "utf-16", "utf-32"])
def test_json_bytes_api_preserves_encoding_detection(encoding):
    assert to_bencode('"é"'.encode(encoding)) == b"2:\xc3\xa9"


@pytest.mark.parametrize("sign", ["", "-"])
def test_large_integer_full_conversion_round_trip(sign):
    text = sign + "1234567890" * 500
    encoded = b"i" + text.encode() + b"e"
    original_limit = sys.get_int_max_str_digits()
    try:
        sys.set_int_max_str_digits(640)
        assert to_json(encoded) == text
        assert to_bencode(text) == encoded
        assert to_bencode(to_json(b"l" + encoded + b"e")) == b"l" + encoded + b"e"
        assert sys.get_int_max_str_digits() == 640
    finally:
        sys.set_int_max_str_digits(original_limit)


@pytest.mark.parametrize("value", [0, -1, 'é\n\\"', [], {}, [1, {}, ["x"]], {"é": [1, {"x": "y"}]}])
def test_json_formatting_matches_standard_library(value):
    assert to_json(to_bencode(json.dumps(value))) == json.dumps(value, indent=4)


def test_json_negative_zero_is_accepted():
    assert to_bencode("-0") == b"i0e"
