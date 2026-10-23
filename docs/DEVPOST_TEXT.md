# Devpost submission text (copy and paste)

**Project name:** PantryPilot

**Tagline:** Alexa+ that remembers your kitchen.

## What it does
PantryPilot is a self-hosted MCP server that gives Alexa+ a persistent household kitchen memory.
You say "I bought six tomatoes, they expire Sunday" and it tracks them. Later you ask "what should
we cook this week?" and it ranks dinners by fewest missing ingredients, uses food that expires first,
respects saved diet and dislikes, and builds one merged shopping list. State persists across sessions.

## Design
A built-in web dashboard (same server, no build step) lets anyone see and try the whole flow:
pantry, expiry watch, meal ideas, one-tap shopping list and food preferences. It talks to the same
MCP endpoint Alexa+ uses, so the demo shows the real tools, not a mock.

## How it was built
Python 3 standard library only (no packages to install). Hand-implemented MCP 2025-11-25 over Streamable HTTP
(initialize, tools/list, tools/call, ping, 202 for notifications, Origin validation, optional bearer
auth). Seven tools with annotations and structured output. Meal suggestions come from a transparent
rule-based ranker, so results are predictable and fast.

## Challenges
Keeping replies short enough for a voice assistant, and making the ranking fair: fewest missing
ingredients first, but food that is about to expire gets a bonus, and diet and dislikes are always respected.

## What's next
Quantity-aware matching, barcode/receipt capture via Fire TV or Ring camera, shared multi-user households.

**Track:** Alexa+
**Mini challenges:** Open Source (new MIT-licensed repo)
