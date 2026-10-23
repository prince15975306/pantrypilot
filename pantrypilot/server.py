
"""PantryPilot MCP server and local web dashboard."""
import json
import os
from pathlib import Path
from urllib.parse import urlsplit
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .tools import TOOLS

SUPPORTED = ["2025-11-25", "2025-06-18", "2025-03-26"]
TOKEN = os.environ.get("MCP_BEARER_TOKEN")
WEB_DIR = Path(__file__).resolve().parent.parent / "web"

WEB_FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/style.css": ("style.css", "text/css; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
}


def ok(i, result):
    return {"jsonrpc": "2.0", "id": i, "result": result}


def err(i, code, message):
    return {"jsonrpc": "2.0", "id": i, "error": {"code": code, "message": message}}


def public_tool(t):
    return {k: v for k, v in t.items() if k != "run"}


def handle(msg: dict):
    i = msg.get("id")
    method = msg.get("method")
    params = msg.get("params") or {}

    if method == "initialize":
        v = params.get("protocolVersion")
        return ok(i, {
            "protocolVersion": v if v in SUPPORTED else SUPPORTED[0],
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {
                "name": "pantrypilot",
                "title": "PantryPilot",
                "version": "1.0.0",
            },
            "instructions": (
                "Kitchen memory for the household: track pantry, remember diet "
                "preferences, suggest meals that use expiring food, and build "
                "shopping lists."
            ),
        })

    if method == "ping":
        return ok(i, {})

    if method == "tools/list":
        return ok(i, {"tools": [public_tool(t) for t in TOOLS]})

    if method == "tools/call":
        tool = next(
            (t for t in TOOLS if t["name"] == params.get("name")),
            None,
        )
        if not tool:
            return err(i, -32602, f"Unknown tool: {params.get('name')}")

        try:
            return ok(i, tool["run"](**(params.get("arguments") or {})))
        except TypeError as e:
            return ok(i, {
                "isError": True,
                "content": [{"type": "text", "text": f"Bad arguments: {e}"}],
            })
        except Exception as e:
            return ok(i, {
                "isError": True,
                "content": [{"type": "text", "text": f"Tool failed: {e}"}],
            })

    return None if i is None else err(i, -32601, f"Method not found: {method}")


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body=None, headers=None):
        data = b"" if body is None else json.dumps(body).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        if data:
            self.wfile.write(data)

    def _send_web_file(self, filename, content_type):
        path = WEB_DIR / filename

        try:
            data = path.read_bytes()
        except OSError:
            return self._send(500, {
                "error": f"Cannot read web/{filename}. Check that the frontend files exist."
            })

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = urlsplit(self.path).path

        if path == "/health":
            return self._send(200, {"status": "ok"})

        if path == "/mcp":
            return self._send(
                405,
                {"error": "Use POST /mcp"},
                {"Allow": "POST"},
            )

        web_file = WEB_FILES.get(path)
        if web_file:
            return self._send_web_file(*web_file)

        return self._send(404, {"error": "Page not found"})

    def do_POST(self):
        if urlsplit(self.path).path != "/mcp":
            return self._send(404, {"error": "Use POST /mcp"})

        origin = self.headers.get("Origin")
        host = self.headers.get("Host", "")
        allowed_origins = {
            item.strip()
            for item in os.environ.get("ALLOWED_ORIGINS", "").split(",")
            if item.strip()
        }

        # Allow same-origin requests and any explicitly configured origins.
        same_origin = origin in (f"http://{host}", f"https://{host}")
        if origin and not same_origin and origin not in allowed_origins:
            return self._send(403, {"error": "Origin not allowed"})

        if TOKEN and self.headers.get("Authorization") != f"Bearer {TOKEN}":
            return self._send(
                401,
                {"error": "Unauthorized"},
                {"WWW-Authenticate": "Bearer"},
            )

        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            return self._send(400, {"error": "Invalid content length"})

        if length > 1_000_000:
            return self._send(413, {"error": "Too large"})

        try:
            body = json.loads(self.rfile.read(length) or b"")
        except (ValueError, UnicodeDecodeError):
            return self._send(400, err(None, -32700, "Parse error"))

        batch = isinstance(body, list)
        messages = body if batch else [body]
        output = []

        for message in messages:
            if (
                not isinstance(message, dict)
                or message.get("jsonrpc") != "2.0"
                or not isinstance(message.get("method"), str)
            ):
                if not (
                    isinstance(message, dict)
                    and "result" in message
                ):
                    output.append(err(
                        message.get("id") if isinstance(message, dict) else None,
                        -32600,
                        "Invalid Request",
                    ))
                continue

            result = handle(message)
            if result is not None:
                output.append(result)

        if not output:
            return self._send(202)

        return self._send(200, output if batch else output[0])

    def log_message(self, fmt, *args):
        pass


def create_server(port: int = 3000) -> ThreadingHTTPServer:
    return ThreadingHTTPServer(
        (os.environ.get("HOST", "127.0.0.1"), port),
        Handler,
    )


def main():
    port = int(os.environ.get("PORT", 3000))
    server = create_server(port)

    print(f"PantryPilot dashboard: http://localhost:{port}/")
    print(f"MCP endpoint:           http://localhost:{port}/mcp")
    print("Press Ctrl+C to stop.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()
