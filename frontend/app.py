from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


HOST = "127.0.0.1"
PORT = 8501
BACKEND_URL = "http://127.0.0.1:8000"
FRONTEND_DIR = Path(__file__).resolve().parent


class FrontendHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND_DIR), **kwargs)

    def do_GET(self):
        if self.path.startswith("/api/"):
            self.proxy_to_backend("GET")
            return

        super().do_GET()

    def do_POST(self):
        if self.path.startswith("/api/"):
            self.proxy_to_backend("POST")
            return

        self.send_error(404)

    def proxy_to_backend(self, method):
        backend_path = self.path.removeprefix("/api")
        body = None
        headers = {"Accept": "application/json"}
        authorization = self.headers.get("Authorization")
        if authorization:
            headers["Authorization"] = authorization
        if method == "POST":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length) if content_length else None
            headers["Content-Type"] = self.headers.get("Content-Type", "application/json")

        request = Request(
            f"{BACKEND_URL}{backend_path}",
            data=body,
            headers=headers,
            method=method,
        )

        try:
            with urlopen(request, timeout=8) as response:
                body = response.read()
                self.send_response(response.status)
                self.send_header("Content-Type", response.headers.get("Content-Type", "application/json"))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(body)
        except HTTPError as error:
            self.send_response(error.code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(error.read())
        except URLError:
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"detail":"Backend API is not reachable on http://127.0.0.1:8000"}')


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), FrontendHandler)
    print(f"Serving PayTrend project page at http://{HOST}:{PORT}/index.html")
    print(f"Proxying frontend API requests from /api to {BACKEND_URL}")
    server.serve_forever()
