"""Built-in recipe book. Ingredient tuples are (name, quantity, unit)."""
RECIPES = [
    {"id": "dal-tadka", "name": "Dal Tadka", "tags": ["vegetarian", "vegan", "indian", "quick"], "minutes": 30,
     "ingredients": [("lentils", 1, "cup"), ("onion", 1, "pc"), ("tomato", 2, "pc"), ("garlic", 4, "clove"), ("cumin", 1, "tsp")]},
    {"id": "veg-fried-rice", "name": "Veg Fried Rice", "tags": ["vegetarian", "vegan", "quick"], "minutes": 20,
     "ingredients": [("rice", 2, "cup"), ("carrot", 1, "pc"), ("onion", 1, "pc"), ("soy sauce", 2, "tbsp"), ("peas", 0.5, "cup")]},
    {"id": "paneer-bhurji", "name": "Paneer Bhurji", "tags": ["vegetarian", "indian", "quick"], "minutes": 20,
     "ingredients": [("paneer", 200, "g"), ("onion", 1, "pc"), ("tomato", 1, "pc"), ("green chilli", 2, "pc")]},
    {"id": "pasta-arrabbiata", "name": "Pasta Arrabbiata", "tags": ["vegetarian", "vegan", "italian", "quick"], "minutes": 25,
     "ingredients": [("pasta", 200, "g"), ("tomato", 4, "pc"), ("garlic", 3, "clove"), ("chilli flakes", 1, "tsp")]},
    {"id": "egg-curry", "name": "Egg Curry", "tags": ["eggetarian", "indian"], "minutes": 35,
     "ingredients": [("egg", 4, "pc"), ("onion", 2, "pc"), ("tomato", 2, "pc"), ("garlic", 3, "clove")]},
    {"id": "chicken-stir-fry", "name": "Chicken Stir Fry", "tags": ["non-veg", "quick"], "minutes": 25,
     "ingredients": [("chicken", 300, "g"), ("bell pepper", 1, "pc"), ("onion", 1, "pc"), ("soy sauce", 2, "tbsp")]},
    {"id": "aloo-paratha", "name": "Aloo Paratha", "tags": ["vegetarian", "indian", "breakfast"], "minutes": 40,
     "ingredients": [("wheat flour", 2, "cup"), ("potato", 3, "pc"), ("green chilli", 1, "pc"), ("butter", 1, "tbsp")]},
    {"id": "tomato-soup", "name": "Tomato Soup", "tags": ["vegetarian", "vegan", "quick"], "minutes": 25,
     "ingredients": [("tomato", 5, "pc"), ("onion", 1, "pc"), ("garlic", 2, "clove")]},
]
