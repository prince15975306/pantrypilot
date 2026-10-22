"""The seven MCP tools exposed to Alexa+."""
from datetime import date

from . import bedrock, store
from .planner import days_left, missing_for, norm, rank_recipes
from .recipes import RECIPES


def text(t, structured=None):
    out = {"content": [{"type": "text", "text": t}]}
    if structured is not None:
        out["structuredContent"] = structured
    return out


def fail(t):
    return {"isError": True, "content": [{"type": "text", "text": t}]}


def add_pantry_item(name="", quantity=1, unit="pc", expires_on=None):
    if not str(name).strip():
        return fail("Please tell me which item to add.")
    if expires_on:
        try:
            date.fromisoformat(expires_on)
        except ValueError:
            return fail("Expiry must look like 2026-10-31.")
    s = store.load()
    item = next((p for p in s["pantry"] if norm(p["name"]) == norm(name)), None)
    if item:
        item["quantity"] += quantity
        if expires_on:
            item["expires_on"] = expires_on
    else:
        new = {"name": norm(name), "quantity": quantity, "unit": unit}
        if expires_on:
            new["expires_on"] = expires_on
        s["pantry"].append(new)
    store.save(s)
    return text(f"Added {quantity} {unit} {name}. You now have {len(s['pantry'])} items.", {"pantry": s["pantry"]})


def use_pantry_item(name="", quantity=1):
    s = store.load()
    item = next((p for p in s["pantry"] if norm(p["name"]) == norm(name)), None)
    if not item:
        return fail(f"I don't see {name} in your pantry.")
    item["quantity"] -= quantity
    if item["quantity"] <= 0:
        s["pantry"].remove(item)
    store.save(s)
    msg = f"{item['quantity']} {item['unit']} of {name} left." if item["quantity"] > 0 else f"{name} is finished and removed."
    return text(msg, {"pantry": s["pantry"]})


def list_pantry():
    pantry = store.load()["pantry"]
    if not pantry:
        return text("Your pantry is empty.", {"pantry": pantry})
    return text(", ".join(f"{p['quantity']} {p['unit']} {p['name']}" for p in pantry) + ".", {"pantry": pantry})


def expiring_soon(days=3):
    items = []
    for p in store.load()["pantry"]:
        if p.get("expires_on") and days_left(p["expires_on"]) <= days:
            items.append({**p, "days_left": days_left(p["expires_on"])})
    items.sort(key=lambda i: i["days_left"])
    if not items:
        return text(f"Nothing expires in the next {days} days.", {"items": items})
    names = ", ".join(f"{i['name']} ({'expired' if i['days_left'] <= 0 else str(i['days_left']) + ' days'})" for i in items)
    return text(names + ".", {"items": items})


def remember_preference(key="", value=""):
    if key not in ("diet", "dislikes", "people"):
        return fail("I can remember diet, dislikes, or number of people.")
    s = store.load()
    s["preferences"][key] = value
    store.save(s)
    return text(f"Got it. I'll remember {key} is {value}.", {"preferences": s["preferences"]})


def suggest_meals(days=3):
    s = store.load()
    ranked = rank_recipes(s["pantry"], s["preferences"], int(min(max(days, 1), 7)))
    if not ranked:
        return text("I couldn't find a recipe that fits your preferences.", {"meals": []})
    meals = [{"id": r["recipe"]["id"], "name": r["recipe"]["name"], "minutes": r["recipe"]["minutes"],
              "missing": [m["name"] for m in r["missing"]]} for r in ranked]
    spoken = ". ".join(
        f"{r['recipe']['name']}, {r['recipe']['minutes']} minutes" +
        (", you need " + " and ".join(m["name"] for m in r["missing"]) if r["missing"] else ", you have everything")
        for r in ranked) + "."
    source = "rules"
    if bedrock.enabled():
        try:
            spoken = bedrock.meal_plan(s["pantry"], s["preferences"], ranked, days) or spoken
            source = "amazon-bedrock"
        except Exception as e:  # fall back to the rule-based plan
            print(f"Bedrock failed, using rule-based plan: {e}")
    return text(spoken, {"meals": meals, "source": source})


def build_shopping_list(recipe_ids=()):
    pantry = store.load()["pantry"]
    merged = {}
    for rid in recipe_ids:
        r = next((x for x in RECIPES if x["id"] == rid), None)
        if not r:
            return fail(f"I don't know the recipe {rid}.")
        for m in missing_for(r, pantry):
            k = norm(m["name"])
            if k in merged:
                merged[k]["quantity"] += m["quantity"]
            else:
                merged[k] = dict(m)
    items = list(merged.values())
    if items:
        msg = "Shopping list: " + ", ".join(f"{i['quantity']} {i['unit']} {i['name']}" for i in items) + "."
    else:
        msg = "You already have everything."
    return text(msg, {"list": items})


def _schema(props, required=()):
    return {"type": "object", "properties": props, "required": list(required)}


TOOLS = [
    {"name": "add_pantry_item", "title": "Add pantry item",
     "description": "Add or top up a food item in the household pantry. Optionally record when it expires (YYYY-MM-DD).",
     "inputSchema": _schema({"name": {"type": "string"}, "quantity": {"type": "number", "default": 1},
                             "unit": {"type": "string", "default": "pc"}, "expires_on": {"type": "string", "description": "YYYY-MM-DD"}}, ["name"]),
     "annotations": {"readOnlyHint": False, "idempotentHint": False}, "run": add_pantry_item},
    {"name": "use_pantry_item", "title": "Use pantry item",
     "description": "Reduce the quantity of an item after cooking; removes it when it runs out.",
     "inputSchema": _schema({"name": {"type": "string"}, "quantity": {"type": "number", "default": 1}}, ["name"]),
     "annotations": {"readOnlyHint": False, "destructiveHint": False}, "run": use_pantry_item},
    {"name": "list_pantry", "title": "List pantry", "description": "Read out everything currently in the pantry.",
     "inputSchema": _schema({}), "annotations": {"readOnlyHint": True}, "run": list_pantry},
    {"name": "expiring_soon", "title": "Expiring soon",
     "description": "List pantry items that expire within the next N days (default 3).",
     "inputSchema": _schema({"days": {"type": "number", "default": 3}}), "annotations": {"readOnlyHint": True}, "run": expiring_soon},
    {"name": "remember_preference", "title": "Remember preference",
     "description": "Store a household preference that persists across sessions, e.g. diet=vegetarian, dislikes='mushroom, okra', people=4.",
     "inputSchema": _schema({"key": {"type": "string", "enum": ["diet", "dislikes", "people"]}, "value": {"type": "string"}}, ["key", "value"]),
     "annotations": {"readOnlyHint": False, "idempotentHint": True}, "run": remember_preference},
    {"name": "suggest_meals", "title": "Suggest meals",
     "description": "Suggest dinners using what is in the pantry, prioritising food that expires soon and respecting saved preferences. Uses Amazon Bedrock for a spoken plan when configured.",
     "inputSchema": _schema({"days": {"type": "number", "default": 3, "minimum": 1, "maximum": 7}}),
     "annotations": {"readOnlyHint": True, "openWorldHint": False}, "run": suggest_meals},
    {"name": "build_shopping_list", "title": "Build shopping list",
     "description": "Given recipe ids (from suggest_meals), return the ingredients missing from the pantry, merged into one shopping list.",
     "inputSchema": _schema({"recipe_ids": {"type": "array", "items": {"type": "string"}}}, ["recipe_ids"]),
     "annotations": {"readOnlyHint": True}, "run": build_shopping_list},
]
