"""PantryPilot MCP server: Streamable HTTP transport, MCP spec 2025-11-25, Python standard library only."""
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .tools import TOOLS

SUPPORTED = ["2025-11-25", "2025-06-18", "2025-03-26"]
TOKEN = os.environ.get("MCP_BEARER_TOKEN")  # optional auth


def ok(i, result):
    return {"jsonrpc": "2.0", "id": i, "result": result}


def err(i, code, message):
    return {"jsonrpc": "2.0", "id": i, "error": {"code": code, "message": message}}


def public_tool(t):
    return {k: v for k, v in t.items() if k != "run"}


def handle(msg: dict):
    i, method, params = msg.get("id"), msg.get("method"), msg.get("params") or {}
    if method == "initialize":
        v = params.get("protocolVersion")
        return ok(i, {
            "protocolVersion": v if v in SUPPORTED else SUPPORTED[0],
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": "pantrypilot", "title": "PantryPilot", "version": "1.0.0"},
            "instructions": "Kitchen memory for the household: track pantry, remember diet preferences, "
                            "suggest meals that use expiring food, and build shopping lists.",
        })
    if method == "ping":
        return ok(i, {})
    if method == "tools/list":
        return ok(i, {"tools": [public_tool(t) for t in TOOLS]})
    if method == "tools/call":
        tool = next((t for t in TOOLS if t["name"] == params.get("name")), None)
        if not tool:
            return err(i, -32602, f"Unknown tool: {params.get('name')}")
        try:
            return ok(i, tool["run"](**(params.get("arguments") or {})))
        except TypeError as e:
            return ok(i, {"isError": True, "content": [{"type": "text", "text": f"Bad arguments: {e}"}]})
        except Exception as e:
            return ok(i, {"isError": True, "content": [{"type": "text", "text": f"Tool failed: {e}"}]})
    return None if i is None else err(i, -32601, f"Method not found: {method}")


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body=None, headers=None):
        data = b"" if body is None else json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/health":
            return self._send(200, {"status": "ok"})
        return self._send(405 if self.path == "/mcp" else 404, {"error": "Use POST /mcp"}, {"Allow": "POST"})

    def do_POST(self):
        if self.path != "/mcp":
            return self._send(404, {"error": "Use POST /mcp"})
        origin = self.headers.get("Origin")  # DNS-rebinding protection
        if origin and origin not in os.environ.get("ALLOWED_ORIGINS", "").split(","):
            return self._send(403, {"error": "Origin not allowed"})
        if TOKEN and self.headers.get("Authorization") != f"Bearer {TOKEN}":
            return self._send(401, {"error": "Unauthorized"}, {"WWW-Authenticate": "Bearer"})
        length = int(self.headers.get("Content-Length") or 0)
        if length > 1_000_000:
            return self._send(413, {"error": "Too large"})
        try:
            body = json.loads(self.rfile.read(length) or b"")
        except ValueError:
            return self._send(400, err(None, -32700, "Parse error"))
        batch = isinstance(body, list)
        out = []
        for m in (body if batch else [body]):
            if not isinstance(m, dict) or m.get("jsonrpc") != "2.0" or not isinstance(m.get("method"), str):
                if not (isinstance(m, dict) and "result" in m):
                    out.append(err(m.get("id") if isinstance(m, dict) else None, -32600, "Invalid Request"))
                continue
            r = handle(m)
            if r is not None:
                out.append(r)
        if not out:
            return self._send(202)  # notifications only
        return self._send(200, out if batch else out[0])

    def log_message(self, fmt, *args):
        pass  # keep the console quiet


def create_server(port: int = 3000) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((os.environ.get("HOST", "127.0.0.1"), port), Handler)


def main():
    port = int(os.environ.get("PORT", 3000))
    srv = create_server(port)
    print(f"PantryPilot MCP listening on http://localhost:{port}/mcp  (Ctrl+C to stop)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
