import argparse
import json
import sys

import bencodepy


def to_json(bencoded_data):
    """Convert bencoded data to JSON."""
    try:
        decoded_data = bencodepy.decode(bencoded_data)
        json_output = json.dumps(decoded_data, indent=4)
        return json_output
    except Exception as e:
        raise ValueError(f"Error decoding bencoded data: {e}")


def to_bencode(json_data):
    """Convert JSON data to bencoded format."""
    try:
        parsed_data = json.loads(json_data)
        bencoded_output = bencodepy.encode(parsed_data)
        return bencoded_output
    except Exception as e:
        raise ValueError(f"Error encoding JSON to bencoded data: {e}")


def try_both():
    """Attempt bencode -> JSON. If that fails, assume input is JSON and try JSON -> bencode."""
    input_data = sys.stdin.read()

    try:
        sys.stdout.write(to_json(input_data.encode()))
    except ValueError:
        try:
            sys.stdout.buffer.write(to_bencode(input_data))
        except ValueError as e:
            print(f"Conversion failed: {e}", file=sys.stderr)
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Convert between JSON and bencode.")
    parser.add_argument(
        "--to-json", action="store_true", help="Convert bencoded input to JSON"
    )
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
        # Default behavior: try to detect and convert automatically
        try_both()


if __name__ == "__main__":
    main()
