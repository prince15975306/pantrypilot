import json
import os
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from datetime import date, timedelta

os.environ["PANTRY_DB"] = os.path.join(tempfile.mkdtemp(), "state.json")
os.environ.pop("BEDROCK_MODEL_ID", None)
from pantrypilot.server import create_server  # noqa: E402


class SmokeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = create_server(0)
        cls.url = f"http://127.0.0.1:{cls.srv.server_address[1]}/mcp"
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.n = 0

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def post(self, payload, headers=None):
        req = urllib.request.Request(self.url, json.dumps(payload).encode(),
                                     {"Content-Type": "application/json", **(headers or {})})
        try:
            with urllib.request.urlopen(req) as r:
                raw = r.read()
                return r.status, json.loads(raw) if raw else None
        except urllib.error.HTTPError as e:
            return e.code, None

    def rpc(self, method, params=None):
        type(self).n += 1
        return self.post({"jsonrpc": "2.0", "id": self.n, "method": method, "params": params or {}})[1]

    def call(self, name, args=None):
        return self.rpc("tools/call", {"name": name, "arguments": args or {}})["result"]

    def test_full_flow(self):
        init = self.rpc("initialize", {"protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {"name": "t", "version": "0"}})
        self.assertEqual(init["result"]["protocolVersion"], "2025-11-25")
        self.assertEqual(self.post({"jsonrpc": "2.0", "method": "notifications/initialized"})[0], 202)
        self.assertEqual(len(self.rpc("tools/list")["result"]["tools"]), 7)

        soon = (date.today() + timedelta(days=1)).isoformat()
        self.call("remember_preference", {"key": "diet", "value": "vegetarian"})
        self.call("add_pantry_item", {"name": "Tomato", "quantity": 6, "expires_on": soon})
        self.call("add_pantry_item", {"name": "onion", "quantity": 3})
        self.call("add_pantry_item", {"name": "garlic", "quantity": 6, "unit": "clove"})
        self.assertIn("tomato", self.call("list_pantry")["content"][0]["text"])
        self.assertIn("tomato", self.call("expiring_soon")["content"][0]["text"])

        meals = self.call("suggest_meals", {"days": 2})["structuredContent"]
        self.assertEqual(meals["source"], "rules")
        self.assertTrue(all("chicken" not in m["id"] for m in meals["meals"]))
        lst = self.call("build_shopping_list", {"recipe_ids": [m["id"] for m in meals["meals"]]})
        self.assertIn("list", lst["structuredContent"])
        self.assertTrue(self.call("use_pantry_item", {"name": "nothing"})["isError"])
        self.assertEqual(self.rpc("bogus")["error"]["code"], -32601)
        self.assertEqual(self.post({}, {"Origin": "https://evil.example"})[0], 403)


if __name__ == "__main__":
    unittest.main()
