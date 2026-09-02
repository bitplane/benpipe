import json

import pytest

from benpipe.benpipe import to_bencode, to_json


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


@pytest.mark.parametrize("invalid_json", ["not json", "1.5"])
def test_to_bencode_reports_invalid_input(invalid_json):
    with pytest.raises(ValueError, match="Error encoding JSON"):
        to_bencode(invalid_json)
