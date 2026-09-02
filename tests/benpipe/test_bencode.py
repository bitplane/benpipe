import sys

import pytest
from hypothesis import given
from hypothesis import strategies as st

from benpipe._bencode import BencodeDict, DecodeError, EncodeError, decode, encode


@pytest.mark.parametrize(
    ("encoded", "value"),
    [
        (b"0:", b""),
        (b"4:spam", b"spam"),
        (b"i0e", 0),
        (b"i3e", 3),
        (b"i-3e", -3),
        (b"l4:spam4:eggse", [b"spam", b"eggs"]),
        (
            b"d3:cow3:moo4:spam4:eggse",
            BencodeDict(((b"cow", b"moo"), (b"spam", b"eggs"))),
        ),
    ],
)
def test_specification_examples(encoded, value):
    assert decode(encoded, strict=True) == value
    assert encode(value) == encoded


@pytest.mark.parametrize(
    ("encoded", "value"),
    [
        (b"i03e", 3),
        (b"i-0e", 0),
        (b"i+1e", 1),
        (b"03:abc", b"abc"),
        (b"d1:bi1e1:ai2ee", BencodeDict(((b"b", 1), (b"a", 2)))),
    ],
)
def test_lenient_decode_accepts_recoverable_noncanonical_input(encoded, value):
    assert decode(encoded) == value


@pytest.mark.parametrize(
    "encoded",
    [
        b"i03e",
        b"i-0e",
        b"i+1e",
        b"03:abc",
        b"d1:bi1e1:ai2ee",
    ],
)
def test_strict_decode_rejects_noncanonical_input(encoded):
    with pytest.raises(DecodeError):
        decode(encoded, strict=True)


@pytest.mark.parametrize(
    "encoded",
    [
        b"",
        b"x",
        b"e",
        b"i",
        b"ie",
        b"i-e",
        b"i1",
        b"-1:a",
        b"1",
        b"1x:a",
        b"4:abc",
        b"l",
        b"d",
        b"di1e1:ae",
        b"d1:ae",
        b"i1ei2e",
    ],
)
def test_malformed_input_raises_decode_error(encoded):
    with pytest.raises(DecodeError):
        decode(encoded)


def test_decode_error_includes_byte_offset():
    with pytest.raises(DecodeError, match=r"at byte 3") as caught:
        decode(b"i1ejunk")

    assert caught.value.offset == 3


def test_decoder_requires_bytes():
    with pytest.raises(TypeError, match="must be bytes"):
        decode(bytearray(b"i1e"))


def test_duplicate_dictionary_keys_are_preserved():
    encoded = b"d1:ai1e1:ai2ee"
    value = BencodeDict(((b"a", 1), (b"a", 2)))

    assert decode(encoded, strict=True) == value
    assert encode(value) == encoded


def test_dictionary_encoding_is_sorted_and_stable():
    value = BencodeDict(((b"z", 1), (b"a", 2), (b"a", 3)))

    assert encode(value) == b"d1:ai2e1:ai3e1:zi1ee"


def test_encoder_handles_deep_nesting_without_recursion():
    value = 1
    for _ in range(sys.getrecursionlimit() + 10):
        value = [value]

    assert decode(encode(value)) == value


def test_arbitrarily_large_integer_avoids_decimal_conversion_limit():
    value = 10**5000

    assert decode(encode(value), strict=True) == value


@pytest.mark.parametrize("value", [True, False, "text", 1.5, None, (), bytearray(b"x")])
def test_encoder_rejects_non_bencode_types(value):
    with pytest.raises(EncodeError):
        encode(value)


def test_encoder_rejects_non_bytes_dictionary_keys():
    with pytest.raises(EncodeError, match="must be bytes"):
        encode({"key": b"value"})


def test_encoder_rejects_cycles():
    value = []
    value.append(value)

    with pytest.raises(EncodeError, match="Cyclic"):
        encode(value)


def test_encoder_rejects_dictionary_cycles():
    value = {}
    value[b"self"] = value

    with pytest.raises(EncodeError, match="Cyclic"):
        encode(value)


scalar_values = st.one_of(st.integers(), st.binary())
bencode_values = st.recursive(
    scalar_values,
    lambda children: st.one_of(
        st.lists(children, max_size=5),
        st.dictionaries(st.binary(max_size=16), children, max_size=5),
        st.lists(st.tuples(st.binary(max_size=16), children), max_size=5).map(
            lambda entries: BencodeDict(tuple(entries))
        ),
    ),
    max_leaves=30,
)


@given(bencode_values)
def test_encoded_values_are_strictly_decodable(value):
    assert encode(decode(encode(value), strict=True)) == encode(value)


@given(st.binary(max_size=100))
def test_arbitrary_input_never_leaks_an_incidental_exception(data):
    try:
        decode(data)
    except DecodeError:
        pass
