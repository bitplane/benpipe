import argparse
import json
import sys

from ._bencode import DecodeError, EncodeError, decode, encode
from .convert import json_object, to_bencode_types, to_json_types


def to_json(bencoded_data):
    """Convert bencoded data to JSON."""
    try:
        decoded_data = decode(bencoded_data)
    except DecodeError as error:
        raise ValueError(f"Error decoding bencoded data: {error}") from error

    converted = to_json_types(decoded_data)

    json_output = json.dumps(converted, indent=4)
    return json_output


def to_bencode(json_data):
    """Convert JSON data to bencoded format."""
    try:
        parsed_data = json.loads(json_data, object_pairs_hook=json_object)
        converted = to_bencode_types(parsed_data)
        return encode(converted)
    except (json.JSONDecodeError, TypeError, ValueError, EncodeError) as error:
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
