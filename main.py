"""
main.py - Top-level Vercel Python Runtime Entrypoint.
Exports 'app', 'application', and 'handler' variables.
"""

import os
import mimetypes

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

def app(environ, start_response):
    path = environ.get("PATH_INFO", "/").lstrip("/")
    if not path or path == "game":
        file_path = os.path.join(BASE_DIR, "index.html")
    else:
        file_path = os.path.join(BASE_DIR, path)

    if os.path.exists(file_path) and os.path.isfile(file_path):
        mime_type, _ = mimetypes.guess_type(file_path)
        mime_type = mime_type or "text/plain"
        if file_path.endswith(".html"):
            mime_type = "text/html; charset=utf-8"
        elif file_path.endswith(".js"):
            mime_type = "application/javascript; charset=utf-8"
        elif file_path.endswith(".css"):
            mime_type = "text/css; charset=utf-8"

        try:
            with open(file_path, "rb") as f:
                content = f.read()
            status = "200 OK"
            headers = [
                ("Content-Type", mime_type),
                ("Content-Length", str(len(content))),
                ("Cache-Control", "public, max-age=3600"),
            ]
            start_response(status, headers)
            return [content]
        except Exception as e:
            status = "500 Internal Server Error"
            headers = [("Content-Type", "text/plain")]
            start_response(status, headers)
            return [str(e).encode("utf-8")]
    else:
        fallback_path = os.path.join(BASE_DIR, "index.html")
        with open(fallback_path, "rb") as f:
            content = f.read()
        status = "200 OK"
        headers = [
            ("Content-Type", "text/html; charset=utf-8"),
            ("Content-Length", str(len(content))),
        ]
        start_response(status, headers)
        return [content]

# Vercel entrypoint exports
handler = app
application = app
