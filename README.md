# 🪈 benpipe

A simple util to convert between json and bencode.

## 📦 install

```bash
pip install benpipe
```

## ▶️ use

```bash
cat file.json | benpipe
cat file.torrent | benpipe
benpipe --to-json < file.torrent
benpipe --to-bencode < file.json
```

Benpipe accepts recoverable non-canonical bencode, but always writes canonical
bencode with dictionary keys sorted as raw bytes. Structurally invalid input is
rejected with a non-zero exit status.

### Binary data and unusual dictionaries

UTF-8 byte strings become ordinary JSON strings. Other byte strings use a
tagged object:

```json
{"__benpipe_bytes__": "/w=="}
```

Dictionaries with binary or duplicate keys use an ordered list of key-value
pairs, preserving information that a JSON object cannot represent:

```json
{"__benpipe_dict__": [["key", 1], ["key", 2]]}
```

Objects that naturally match either tag are escaped through the dictionary
representation, so conversion remains lossless.

## 🔗 Links

* [🐱 github](https://github.com/bitplane/benpipe)
* [🐍 pypi](https://pypi.org/project/benpipe)
* [🏠 home](https://bitplane.net/dev/python/benpipe)
* [📖 pydoc](https://bitplane.net/dev/python/benpipe/pydoc)
