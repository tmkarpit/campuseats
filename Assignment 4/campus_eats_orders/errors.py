"""RFC 7807-inspired error responses shared by every endpoint."""

import json


def problem(status, title, detail, type_="about:blank"):
    return status, {"Content-Type": "application/problem+json"}, json.dumps(
        {"type": type_, "title": title, "status": status, "detail": detail}
    ).encode("utf-8")
