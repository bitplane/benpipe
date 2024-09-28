import argparse
import json
import sys

import bencodepy

from .convert import to_bencode_types, to_json_types


def to_json(bencoded_data):
    """Convert bencoded data to JSON."""
    try:
        decoded_data = bencodepy.decode(bencoded_data)
    except Exception as e:
        raise ValueError(f"Error decoding bencoded data: {e}")

    converted = to_json_types(decoded_data)

    json_output = json.dumps(converted, indent=4)
    return json_output


def to_bencode(json_data):
    """Convert JSON data to bencoded format."""
    try:
        parsed_data = json.loads(json_data)
    except Exception as e:
        raise ValueError(f"Error encoding JSON to bencoded data: {e}")

    converted = to_bencode_types(parsed_data)

    bencoded_output = bencodepy.encode(converted)
    return bencoded_output


def main():
    parser = argparse.ArgumentParser(description="Convert between JSON and bencode.")
    parser.add_argument("--to-json", action="store_true", help="Convert bencoded input to JSON")
    parser.add_argument(
        "--to-bencode", action="store_true", help="Convert JSON input to bencoded data."
    )

    args = parser.parse_args()

    if args.to_json:
        input_data = sys.stdin.buffer.read()
        sys.stdout.write(to_json(input_data))
    elif args.to_bencode:
        input_data = sys.stdin.read()
        sys.stdout.buffer.write(to_bencode(input_data))
    else:
        try:
            input_data = sys.stdin.buffer.read()
            sys.stdout.write(to_json(input_data))
        except ValueError as json_err:
            print("trying bencode to json")
            try:
                sys.stdout.buffer.write(to_bencode(input_data.decode()))
            except (ValueError, UnicodeDecodeError) as bencode_error:
                print(f"Conversion failed: {json_err} / {bencode_error}", file=sys.stderr)


if __name__ == "__main__":
    main()
