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
```

JSON conversion supports up to 100 nested containers, including the objects and
lists used to represent binary data and dictionary entries. Deeper inputs fail
with a conversion error. The low-level bencode codec has no nesting limit.

## 🔗 Links

* [🐱 github](https://github.com/bitplane/benpipe)
* [🐍 pypi](https://pypi.org/project/benpipe)
* [🏠 home](https://bitplane.net/dev/python/benpipe)
* [📖 pydoc](https://bitplane.net/dev/python/benpipe/pydoc)
