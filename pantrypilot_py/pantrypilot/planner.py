"""Recipe ranking: fewest missing items, expiring food first, diet and dislikes respected."""
from datetime import date

from .recipes import RECIPES


def norm(s) -> str:
    return str(s).strip().lower()


def days_left(iso: str) -> int:
    return (date.fromisoformat(iso) - date.today()).days


def missing_for(recipe: dict, pantry: list) -> list:
    have = {norm(p["name"]) for p in pantry}
    return [{"name": n, "quantity": q, "unit": u} for n, q, u in recipe["ingredients"] if norm(n) not in have]


def expiry_bonus(recipe: dict, pantry: list) -> int:
    bonus = 0
    for n, _, _ in recipe["ingredients"]:
        item = next((p for p in pantry if norm(p["name"]) == norm(n)), None)
        if item and item.get("expires_on") and days_left(item["expires_on"]) <= 3:
            bonus += 2
    return bonus


def _diet_ok(recipe: dict, diet: str) -> bool:
    tags = recipe["tags"]
    if not diet or diet == "any":
        return True
    if diet == "vegan":
        return "vegan" in tags
    if diet == "vegetarian":
        return "vegetarian" in tags or "vegan" in tags
    if diet == "eggetarian":
        return "non-veg" not in tags
    return True


def rank_recipes(pantry: list, prefs: dict | None = None, limit: int = 3) -> list:
    prefs = prefs or {}
    diet = norm(prefs.get("diet", ""))
    dislikes = {norm(x) for x in str(prefs.get("dislikes", "")).split(",") if x.strip()}
    ranked = []
    for r in RECIPES:
        if not _diet_ok(r, diet) or any(norm(n) in dislikes for n, _, _ in r["ingredients"]):
            continue
        missing = missing_for(r, pantry)
        score = len(r["ingredients"]) - len(missing) * 2 + expiry_bonus(r, pantry)
        ranked.append({"recipe": r, "missing": missing, "score": score})
    ranked.sort(key=lambda x: (-x["score"], x["recipe"]["minutes"]))
    return ranked[:limit]
