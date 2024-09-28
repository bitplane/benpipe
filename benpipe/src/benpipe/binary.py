import base64
import json


class Base64Encoder(json.JSONEncoder):
    """
    Write binary data as base64 if it isn't UTF8
    """

    def default(self, obj):
        if isinstance(obj, bytes):
            try:
                return obj.decode("utf-8")
            except UnicodeDecodeError:
                return {"__base64": base64.b64encode(obj).decode("ascii")}

        return json.JSONEncoder.default(self, obj)


def base64_decoder(obj):
    if "__base64" in obj:
        obj = base64.b64decode(obj["__base64"])
    return obj
