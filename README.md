# PantryPilot: a kitchen memory for Alexa+

PantryPilot is a self-hosted **MCP server** (spec **2025-11-25**, **Streamable HTTP**) for the
**Alexa+ track** of the Build, Ship, Shape Amazon Developer Hackathon. Pure **Python 3**, standard
library only.

It gives Alexa+ a memory that lasts between sessions: what is in your pantry, what expires soon,
your household's diet and dislikes. It turns that into dinner suggestions and a shopping list.
Optional **Amazon Bedrock** integration writes the spoken meal plan (AWS Builder mini challenge).

## Tools

| Tool | What it does |
|---|---|
| `add_pantry_item` | Add or top up an item, with optional expiry date |
| `use_pantry_item` | Reduce quantity after cooking |
| `list_pantry` | Read out the pantry |
| `expiring_soon` | Items expiring within N days |
| `remember_preference` | Persist diet, dislikes, household size |
| `suggest_meals` | Rank recipes by fewest missing items, expiring food first, diet respected |
| `build_shopping_list` | Merge missing ingredients across chosen recipes |

State lives in `data/state.json`, so it persists across sessions.

## Run it (Python 3.10+)

```bash
git clone https://github.com/<your-username>/pantrypilot-mcp.git
cd pantrypilot-mcp
python -m unittest discover -s tests -v    # tests
python -m pantrypilot                      # server on http://localhost:3000/mcp
```

On Windows you can also use `py` instead of `python`. In VS Code: open the folder, then
Run and Debug, then "Run PantryPilot server" or "Run tests".

Quick check from a second terminal:

```bash
curl http://localhost:3000/health
curl http://localhost:3000/mcp -H "Content-Type: application/json" -d "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/list\"}"
```

## Optional: Amazon Bedrock

```bash
pip install boto3
set AWS_REGION=us-east-1                 # PowerShell: $env:AWS_REGION="us-east-1"
set BEDROCK_MODEL_ID=<a Claude model ID enabled in your Bedrock console>
python -m pantrypilot
```

With `BEDROCK_MODEL_ID` set, `suggest_meals` calls the Bedrock Converse API and returns
`source: "amazon-bedrock"`. If the call fails it falls back to the rule-based plan.

## Config

| Env var | Purpose |
|---|---|
| `PORT` | Port (default 3000) |
| `HOST` | Bind address (default 127.0.0.1) |
| `MCP_BEARER_TOKEN` | If set, requests need `Authorization: Bearer <token>` |
| `ALLOWED_ORIGINS` | Comma-separated browser origins allowed (default: none) |
| `PANTRY_DB` | Path of the state file |

## Making it reachable by Alexa+

Alexa+ needs a public HTTPS URL. Deploy to any host (AWS App Runner, EC2, Render) or tunnel for
the demo (`cloudflared tunnel --url http://localhost:3000`), then register `https://<host>/mcp`
following the Alexa+ MCP docs.

## License

MIT
