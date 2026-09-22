"""RFC 7807-inspired JSON error representations shared by every endpoint."""


def problem(status, title, detail, type_="about:blank"):
    return {"type": type_, "title": title, "status": status, "detail": detail}
