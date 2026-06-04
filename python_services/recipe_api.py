from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import re
from urllib.parse import parse_qs, urlparse


RECIPES = [
    {
        "id": "chicken-rice-bowl",
        "name": "Chicken Rice Power Bowl",
        "description": "Balanced lunch bowl with lean protein, rice, vegetables, and yogurt sauce.",
        "ingredients": ["chicken breast", "rice", "cucumber", "tomato", "yogurt"],
        "optionalIngredients": ["lemon", "parsley", "olive oil"],
        "calories": 520,
        "proteinGrams": 42,
        "carbsGrams": 58,
        "fatGrams": 13,
        "prepMinutes": 25,
        "tags": ["high-protein", "lunch", "balanced"],
    },
    {
        "id": "tuna-pasta-salad",
        "name": "Tuna Pasta Salad",
        "description": "Quick high-protein meal using pantry tuna and vegetables.",
        "ingredients": ["tuna", "pasta", "cucumber", "corn", "yogurt"],
        "optionalIngredients": ["lemon", "black pepper", "lettuce"],
        "calories": 470,
        "proteinGrams": 34,
        "carbsGrams": 62,
        "fatGrams": 9,
        "prepMinutes": 15,
        "tags": ["high-protein", "quick", "lunch"],
    },
    {
        "id": "egg-avocado-toast",
        "name": "Egg Avocado Toast",
        "description": "Simple breakfast with healthy fats and steady protein.",
        "ingredients": ["eggs", "bread", "avocado", "tomato"],
        "optionalIngredients": ["lemon", "chili flakes", "lettuce"],
        "calories": 390,
        "proteinGrams": 20,
        "carbsGrams": 34,
        "fatGrams": 20,
        "prepMinutes": 12,
        "tags": ["breakfast", "vegetarian", "quick"],
    },
    {
        "id": "lentil-soup",
        "name": "Lentil Vegetable Soup",
        "description": "Warm vegetarian soup rich in fiber and plant protein.",
        "ingredients": ["lentils", "carrot", "onion", "tomato", "potato"],
        "optionalIngredients": ["cumin", "lemon", "parsley"],
        "calories": 360,
        "proteinGrams": 21,
        "carbsGrams": 62,
        "fatGrams": 4,
        "prepMinutes": 35,
        "tags": ["vegetarian", "high-fiber", "dinner"],
    },
    {
        "id": "oats-yogurt-bowl",
        "name": "Oats Yogurt Bowl",
        "description": "No-cook breakfast bowl with fruit, oats, and yogurt.",
        "ingredients": ["oats", "yogurt", "banana", "apple"],
        "optionalIngredients": ["cinnamon", "nuts", "honey"],
        "calories": 410,
        "proteinGrams": 19,
        "carbsGrams": 68,
        "fatGrams": 8,
        "prepMinutes": 7,
        "tags": ["breakfast", "vegetarian", "quick"],
    },
    {
        "id": "chickpea-salad-wrap",
        "name": "Chickpea Salad Wrap",
        "description": "Fresh vegetarian wrap with chickpeas and crunchy vegetables.",
        "ingredients": ["chickpeas", "bread", "cucumber", "tomato", "lettuce"],
        "optionalIngredients": ["yogurt", "lemon", "tahini"],
        "calories": 430,
        "proteinGrams": 18,
        "carbsGrams": 66,
        "fatGrams": 11,
        "prepMinutes": 12,
        "tags": ["vegetarian", "high-fiber", "lunch"],
    },
]


ALIASES = {
    "chicken": "chicken breast",
    "دجاج": "chicken breast",
    "صدر دجاج": "chicken breast",
    "رز": "rice",
    "ارز": "rice",
    "خيار": "cucumber",
    "بندورة": "tomato",
    "طماطم": "tomato",
    "لبن": "yogurt",
    "زبادي": "yogurt",
    "تونة": "tuna",
    "معكرونة": "pasta",
    "مكرونة": "pasta",
    "بيض": "eggs",
    "خبز": "bread",
    "افوكادو": "avocado",
    "عدس": "lentils",
    "جزر": "carrot",
    "بصل": "onion",
    "بطاطا": "potato",
    "شوفان": "oats",
    "موز": "banana",
    "تفاح": "apple",
    "حمص": "chickpeas",
    "خس": "lettuce",
    "ذرة": "corn",
}


def split_ingredients(raw):
    return [item.strip() for item in re.split(r"[\n,،]+", raw) if item.strip()]


def normalize_ingredient(value):
    lowered = value.strip().lower()
    return ALIASES.get(lowered, lowered)


def recommend_recipes(ingredients, max_calories=None, min_protein_grams=None, tags=None):
    available = {normalize_ingredient(item) for item in ingredients}
    requested_tags = {tag.strip().lower() for tag in (tags or []) if tag.strip()}
    recommendations = []

    for recipe in RECIPES:
        if max_calories and recipe["calories"] > max_calories:
            continue
        if min_protein_grams and recipe["proteinGrams"] < min_protein_grams:
            continue
        if requested_tags and not any(tag in requested_tags for tag in recipe["tags"]):
            continue

        required = [normalize_ingredient(item) for item in recipe["ingredients"]]
        optional = [normalize_ingredient(item) for item in recipe["optionalIngredients"]]
        matched = [item for item in required if item in available]
        missing = [item for item in required if item not in available]
        available_optional = [item for item in optional if item in available]
        match_percentage = round((len(matched) / len(required)) * 100)

        if match_percentage == 0:
            continue

        recommendations.append(
            {
                **recipe,
                "matchPercentage": match_percentage,
                "matchedIngredients": matched,
                "missingIngredients": missing,
                "availableOptionalIngredients": available_optional,
                "reason": (
                    "You have all required ingredients."
                    if not missing
                    else f"You have {len(matched)} of {len(required)} required ingredients."
                ),
            }
        )

    return sorted(
        recommendations,
        key=lambda item: (-item["matchPercentage"], -item["proteinGrams"], item["calories"]),
    )


class RecipeHandler(BaseHTTPRequestHandler):
    def _send_html(self, status_code, html):
        body = html.encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, status_code, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self._send_json(200, {"ok": True})

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path in ["/", "/recipes"]:
            self._send_html(200, RECIPES_PAGE)
            return

        if parsed.path == "/health":
            self._send_json(200, {"ok": True})
            return

        if parsed.path == "/recipes/dataset":
            self._send_json(200, {"recipes": RECIPES})
            return

        if parsed.path == "/recipes/search":
            query = parse_qs(parsed.query)
            ingredients = split_ingredients(query.get("ingredients", [""])[0])
            if not ingredients:
                self._send_json(400, {"error": "Pass ingredients query, for example ?ingredients=دجاج،رز"})
                return

            max_calories = query.get("maxCalories", [None])[0]
            min_protein = query.get("minProteinGrams", [None])[0]
            recommendations = recommend_recipes(
                ingredients=ingredients,
                max_calories=float(max_calories) if max_calories else None,
                min_protein_grams=float(min_protein) if min_protein else None,
            )
            self._send_json(200, {"recommendations": recommendations})
            return

        self._send_json(404, {"error": "Not found"})

    def do_POST(self):
        if self.path != "/recipes/search":
            self._send_json(404, {"error": "Not found"})
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length).decode("utf-8")

        try:
            payload = json.loads(raw_body)
        except json.JSONDecodeError:
            self._send_json(400, {"error": "Invalid JSON body"})
            return

        ingredients = payload.get("ingredients", [])
        if isinstance(ingredients, str):
            ingredients = split_ingredients(ingredients)

        if not ingredients:
            self._send_json(400, {"error": "ingredients is required"})
            return

        recommendations = recommend_recipes(
            ingredients=ingredients,
            max_calories=payload.get("maxCalories"),
            min_protein_grams=payload.get("minProteinGrams"),
            tags=payload.get("tags"),
        )

        self._send_json(200, {"recommendations": recommendations})


def run(host="127.0.0.1", port=5055):
    server = HTTPServer((host, port), RecipeHandler)
    print(f"Recipe API running on http://{host}:{port}")
    server.serve_forever()


RECIPES_PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Healthy Recipe Finder</title>
  <style>
    body {
      margin: 0;
      font-family: Arial, sans-serif;
      background: #f6f7f9;
      color: #17212b;
    }
    main {
      max-width: 960px;
      margin: 36px auto;
      padding: 0 18px;
    }
    h1 {
      margin: 0 0 18px;
      font-size: 28px;
    }
    textarea {
      width: 100%;
      min-height: 110px;
      box-sizing: border-box;
      padding: 12px;
      border: 1px solid #cbd5df;
      border-radius: 8px;
      font: 16px/1.5 Arial, sans-serif;
      resize: vertical;
    }
    button {
      margin-top: 12px;
      padding: 11px 18px;
      border: 0;
      border-radius: 8px;
      background: #176b5f;
      color: white;
      font-weight: 700;
      cursor: pointer;
    }
    #results {
      display: grid;
      gap: 12px;
      margin-top: 22px;
    }
    article {
      background: white;
      border: 1px solid #d8dee6;
      border-radius: 8px;
      padding: 16px;
    }
    h2 {
      margin: 0 0 6px;
      font-size: 20px;
    }
    .meta {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin: 12px 0;
    }
    .pill {
      padding: 5px 9px;
      border-radius: 999px;
      background: #edf3f1;
      color: #176b5f;
      font-size: 13px;
      font-weight: 700;
    }
    .missing {
      color: #9a3412;
    }
  </style>
</head>
<body>
  <main>
    <h1>Healthy Recipe Finder</h1>
    <textarea id="ingredients">دجاج، رز، خيار، بندورة، لبن</textarea>
    <br />
    <button id="search">Find recipes</button>
    <section id="results"></section>
  </main>

  <script>
    const ingredients = document.getElementById("ingredients");
    const search = document.getElementById("search");
    const results = document.getElementById("results");

    function splitIngredients(value) {
      return value.split(/[\\n,،]+/).map((item) => item.trim()).filter(Boolean);
    }

    function render(recipes) {
      if (!recipes.length) {
        results.innerHTML = "<article>No matching recipes found.</article>";
        return;
      }

      results.innerHTML = recipes.map((recipe) => `
        <article>
          <h2>${recipe.name}</h2>
          <p>${recipe.description}</p>
          <div class="meta">
            <span class="pill">${recipe.matchPercentage}% match</span>
            <span class="pill">${recipe.calories} kcal</span>
            <span class="pill">${recipe.proteinGrams}g protein</span>
            <span class="pill">${recipe.prepMinutes} min</span>
          </div>
          <p><strong>Available:</strong> ${recipe.matchedIngredients.join(", ") || "none"}</p>
          <p class="missing"><strong>Missing:</strong> ${recipe.missingIngredients.join(", ") || "none"}</p>
          <p><strong>Why:</strong> ${recipe.reason}</p>
        </article>
      `).join("");
    }

    async function findRecipes() {
      results.innerHTML = "<article>Searching...</article>";
      const response = await fetch("/recipes/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ingredients: splitIngredients(ingredients.value) })
      });
      const data = await response.json();
      render(data.recommendations || []);
    }

    search.addEventListener("click", findRecipes);
    findRecipes();
  </script>
</body>
</html>"""


if __name__ == "__main__":
    run()
