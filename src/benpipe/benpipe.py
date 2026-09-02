import argparse
import json
import sys

import bencodepy
from bencodepy.decoder import Decoder

from .convert import to_bencode_types, to_json_types


def decode_one(bencoded_data: bytes):
    decoder = Decoder(bencoded_data)
    decoded_data = decoder.decode()

    if decoder.idx != len(bencoded_data):
        raise bencodepy.DecodingError(f"Trailing data at byte {decoder.idx}")

    if bencoded_data[:1] not in (b"d", b"l"):
        if len(decoded_data) != 1:
            raise bencodepy.DecodingError("Expected exactly one top-level value")
        return decoded_data[0]

    return decoded_data


def to_json(bencoded_data):
    """Convert bencoded data to JSON."""
    try:
        decoded_data = decode_one(bencoded_data)
    except bencodepy.DecodingError as error:
        raise ValueError(f"Error decoding bencoded data: {error}") from error

    converted = to_json_types(decoded_data)

    json_output = json.dumps(converted, indent=4)
    return json_output


def to_bencode(json_data):
    """Convert JSON data to bencoded format."""
    try:
        parsed_data = json.loads(json_data)
        converted = to_bencode_types(parsed_data)
        return bencodepy.encode(converted)
    except (json.JSONDecodeError, TypeError, ValueError, bencodepy.EncodingError) as error:
        raise ValueError(f"Error encoding JSON to bencoded data: {error}") from error


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert between JSON and bencode.")
    output_format = parser.add_mutually_exclusive_group()
    output_format.add_argument("--to-json", action="store_true", help="Convert bencoded input to JSON")
    output_format.add_argument("--to-bencode", action="store_true", help="Convert JSON input to bencoded data.")

    args = parser.parse_args()

    if args.to_json:
        try:
            input_data = sys.stdin.buffer.read()
            sys.stdout.write(to_json(input_data))
        except ValueError as error:
            print(f"Conversion failed: {error}", file=sys.stderr)
            return 1
    elif args.to_bencode:
        try:
            input_data = sys.stdin.read()
            sys.stdout.buffer.write(to_bencode(input_data))
        except (ValueError, UnicodeDecodeError) as error:
            print(f"Conversion failed: {error}", file=sys.stderr)
            return 1
    else:
        try:
            input_data = sys.stdin.buffer.read()
            sys.stdout.write(to_json(input_data))
        except ValueError as bencode_error:
            try:
                sys.stdout.buffer.write(to_bencode(input_data.decode()))
            except (ValueError, UnicodeDecodeError) as json_error:
                print(f"Conversion failed: {bencode_error} / {json_error}", file=sys.stderr)
                return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
