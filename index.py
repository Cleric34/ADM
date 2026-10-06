"""
index.py - Official Vercel Python Runtime Entrypoint.
Implements BaseHTTPRequestHandler and WSGI app to serve the 3D Chakravyuha Game.
"""

from http.server import BaseHTTPRequestHandler
import os
import mimetypes

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_file_response(path_str):
    path = path_str.split("?")[0].lstrip("/")
    if not path or path == "game":
        file_path = os.path.join(BASE_DIR, "index.html")
    else:
        file_path = os.path.join(BASE_DIR, path)

    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        file_path = os.path.join(BASE_DIR, "index.html")

    mime_type, _ = mimetypes.guess_type(file_path)
    mime_type = mime_type or "text/html; charset=utf-8"
    if file_path.endswith(".html"):
        mime_type = "text/html; charset=utf-8"
    elif file_path.endswith(".js"):
        mime_type = "application/javascript; charset=utf-8"
    elif file_path.endswith(".css"):
        mime_type = "text/css; charset=utf-8"

    with open(file_path, "rb") as f:
        content = f.read()

    return 200, mime_type, content

# 1. BaseHTTPRequestHandler for Vercel Serverless Function
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            status, mime_type, content = get_file_response(self.path)
            self.send_response(status)
            self.send_header("Content-Type", mime_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "public, max-age=3600")
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(str(e).encode("utf-8"))

    def do_HEAD(self):
        try:
            status, mime_type, content = get_file_response(self.path)
            self.send_response(status)
            self.send_header("Content-Type", mime_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
        except Exception:
            self.send_response(500)
            self.end_headers()

# 2. WSGI Application fallback
def app(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    status_code, mime_type, content = get_file_response(path)
    status_str = f"{status_code} OK" if status_code == 200 else f"{status_code} Error"
    headers = [
        ("Content-Type", mime_type),
        ("Content-Length", str(len(content))),
        ("Cache-Control", "public, max-age=3600"),
    ]
    start_response(status_str, headers)
    return [content]

application = app
