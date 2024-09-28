from benpipe.convert import bytes_to_str, str_to_bytes, to_bencode_types, to_json_types


def test_bytes_to_str_utf8():
    assert bytes_to_str(b"hello") == "hello"


def test_bytes_to_str_non_utf8():
    # This will test non-UTF8 bytes (random example)
    assert bytes_to_str(b"\xff\xfe\xfd") == "__base64://79"


def test_str_to_bytes_utf8():
    assert str_to_bytes("hello") == b"hello"


def test_str_to_bytes_base64():
    # This tests the reverse operation of encoding to base64 and should decode correctly
    assert str_to_bytes("__base64://79") == b"\xff\xfe\xfd"


def test_to_json_types_with_simple_data():
    assert to_json_types({"key": b"hello"}) == {"key": "hello"}


def test_to_json_types_with_binary_data():
    input_data = {b"\xff\xfe\xfd": b"\xfa\xfb\xfc"}
    expected_output = {"__base64://79": "__base64:+vv8"}

    assert to_json_types(input_data) == expected_output


def test_to_bencode_types_with_simple_data():
    assert to_bencode_types({"key": "value"}) == {b"key": b"value"}


def test_tuple_to_json():
    input_tuple = (123, b"\x01\x02\x03")

    json_data = to_json_types({"tuple": input_tuple})

    assert json_data == {"tuple": {"__tuple": [123, "\x01\x02\x03"]}}


def test_json_to_tuple():
    json_data = {"tuple": {"__tuple": [123, "__base64:AgM="]}}

    bencode_data = to_bencode_types(json_data)

    assert bencode_data == {b"tuple": (123, b"\x02\x03")}
