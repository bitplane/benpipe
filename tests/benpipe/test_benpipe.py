import json

import pytest

from benpipe.benpipe import to_json


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
