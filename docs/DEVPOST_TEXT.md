# Devpost submission text (copy and paste)

**Project name:** PantryPilot

**Tagline:** Alexa+ that remembers your kitchen.

## What it does
PantryPilot is a self-hosted MCP server that gives Alexa+ a persistent household kitchen memory.
You say "I bought six tomatoes, they expire Sunday" and it tracks them. Later you ask "what should
we cook this week?" and it ranks dinners by fewest missing ingredients, uses food that expires first,
respects saved diet and dislikes, and builds one merged shopping list. State persists across sessions.

## How it was built
Python 3 standard library only (no packages to install). Hand-implemented MCP 2025-11-25 over Streamable HTTP
(initialize, tools/list, tools/call, ping, 202 for notifications, Origin validation, optional bearer
auth). Seven tools with annotations and structured output. Optional Amazon Bedrock Converse API call
turns ranked candidates into a short spoken plan; falls back to rules if unavailable.

## Challenges
Keeping replies short enough for voice, and grounding the model on the ranked candidates so it
only suggests recipes it can build a shopping list for.

## What's next
Quantity-aware matching, barcode/receipt capture via Fire TV or Ring camera, shared multi-user households.

**Track:** Alexa+
**Mini challenges:** AWS Builder (Amazon Bedrock), Open Source (new MIT-licensed repo)
