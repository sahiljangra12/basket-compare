"""Build docs/catalog.json: the product list shared by the browser app and the Python server.

Each row: name, category, icon, sample price at the usual size, usual size, short description,
other names people type (comma-separated). Prices are SAMPLE prices for demo mode only.
Icons are Microsoft Fluent Emoji (MIT licence), copied into docs/icons/ by this script.

Run:  python scripts/build_catalog.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ITEMS = [
    # Fruit
    ("Red seedless grapes", "Fruit", "grapes", 2.49, "per lb", "Sweet and crisp, no seeds", "red grapes, grape"),
    ("Green seedless grapes", "Fruit", "grapes", 2.59, "per lb", "Tart-sweet and firm", "green grapes, white grapes, grape"),
    ("Bananas", "Fruit", "banana", 0.62, "per lb", "About three bananas to a pound", "banana"),
    ("Organic bananas", "Fruit", "banana", 0.89, "per lb", "Certified organic, sold by the pound", "organic banana"),
    ("Gala apples", "Fruit", "red-apple", 4.49, "3 lb bag", "Mild, sweet and crunchy", "apple, apples, red apple"),
    ("Honeycrisp apples", "Fruit", "red-apple", 2.99, "per lb", "Extra juicy and crisp", "honeycrisp, apple"),
    ("Granny Smith apples", "Fruit", "green-apple", 1.99, "per lb", "Tart green apple, great for baking", "green apple, granny smith, apple"),
    ("Strawberries", "Fruit", "strawberry", 3.49, "16 oz", "Sweet berries in a 1 lb clamshell", "strawberry, berries"),
    ("Blueberries", "Fruit", "blueberries", 3.99, "11 oz", "Plump, sweet-tart berries", "blueberry, berries"),
    ("Raspberries", "Fruit", "strawberry", 3.99, "6 oz", "Delicate, sweet-tart berries", "raspberry, berries"),
    ("Navel oranges", "Fruit", "tangerine", 5.99, "4 lb bag", "Seedless and easy to peel", "orange, oranges"),
    ("Clementines", "Fruit", "tangerine", 5.49, "3 lb bag", "Small, sweet, easy-peel citrus", "cuties, mandarins, mandarin, halos"),
    ("Lemons", "Fruit", "lemon", 0.69, "1 ct", "Bright and juicy", "lemon"),
    ("Limes", "Fruit", "lime", 0.39, "1 ct", "Tart, for drinks and tacos", "lime"),
    ("Hass avocados", "Fruit", "avocado", 1.29, "1 ct", "Creamy; ripe when it yields slightly", "avocado, avocados, guacamole"),
    ("Pineapple", "Fruit", "pineapple", 2.99, "1 ct", "Whole fresh pineapple", "pineapples"),
    ("Mango", "Fruit", "mango", 1.29, "1 ct", "Sweet tropical fruit", "mangoes, mangos"),
    ("Seedless watermelon", "Fruit", "watermelon", 6.99, "1 ct", "Whole melon, about 15 lb", "watermelon, melon"),
    ("Cantaloupe", "Fruit", "melon", 3.49, "1 ct", "Sweet orange melon", "melon, muskmelon"),
    ("Bartlett pears", "Fruit", "pear", 1.79, "per lb", "Soft and sweet when ripe", "pear, pears"),
    ("Peaches", "Fruit", "peach", 2.49, "per lb", "Juicy stone fruit", "peach"),
    ("Cherries", "Fruit", "cherries", 5.99, "per lb", "Sweet dark cherries", "cherry"),
    ("Kiwi", "Fruit", "kiwi-fruit", 0.59, "1 ct", "Tangy green fruit", "kiwis, kiwifruit"),
    ("Coconut", "Fruit", "coconut", 2.99, "1 ct", "Whole brown coconut", "coconuts"),
    # Vegetables
    ("Roma tomatoes", "Vegetables", "tomato", 1.49, "per lb", "Meaty tomatoes for sauces and salsa", "tomato, tomatoes"),
    ("Cherry tomatoes", "Vegetables", "tomato", 3.49, "10 oz", "Bite-size and sweet", "grape tomatoes, tomato"),
    ("Yellow onions", "Vegetables", "onion", 2.99, "3 lb bag", "All-purpose cooking onion", "onion, onions"),
    ("Red onions", "Vegetables", "onion", 1.49, "per lb", "Mild and colorful, good raw", "red onion, onion"),
    ("Garlic", "Vegetables", "garlic", 0.69, "1 ct", "One whole bulb", "garlic bulb"),
    ("Ginger root", "Vegetables", "ginger-root", 3.99, "per lb", "Fresh, spicy root", "ginger"),
    ("Russet potatoes", "Vegetables", "potato", 4.49, "5 lb bag", "For baking, mashing and fries", "potato, potatoes, aloo"),
    ("Sweet potatoes", "Vegetables", "roasted-sweet-potato", 1.29, "per lb", "Naturally sweet, orange flesh", "sweet potato, yams, yam"),
    ("Carrots", "Vegetables", "carrot", 1.29, "2 lb bag", "Crunchy whole carrots", "carrot"),
    ("Baby carrots", "Vegetables", "carrot", 1.69, "16 oz", "Peeled and ready to snack", "carrot, carrots"),
    ("Broccoli crowns", "Vegetables", "broccoli", 1.99, "per lb", "Fresh green crowns", "broccoli"),
    ("Iceberg lettuce", "Vegetables", "leafy-green", 1.79, "1 ct", "Crisp, mild head of lettuce", "lettuce"),
    ("Romaine hearts", "Vegetables", "leafy-green", 3.99, "3 ct", "Crunchy leaves for salads", "romaine, lettuce"),
    ("Baby spinach", "Vegetables", "leafy-green", 3.49, "5 oz", "Tender, pre-washed leaves", "spinach, palak"),
    ("Spring mix salad", "Vegetables", "green-salad", 3.99, "5 oz", "Mixed baby greens", "salad, mixed greens"),
    ("Cucumbers", "Vegetables", "cucumber", 0.79, "1 ct", "Cool and crunchy", "cucumber, kheera"),
    ("Green bell peppers", "Vegetables", "bell-pepper", 0.99, "1 ct", "Crisp and mildly bitter", "bell pepper, capsicum, pepper"),
    ("Red bell peppers", "Vegetables", "bell-pepper", 1.69, "1 ct", "Sweet and crunchy", "bell pepper, capsicum, pepper"),
    ("Jalapeño peppers", "Vegetables", "hot-pepper", 1.99, "per lb", "Medium heat chili", "jalapeno, chili, chilli, green chili"),
    ("White mushrooms", "Vegetables", "mushroom", 2.49, "8 oz", "Sliced or whole button mushrooms", "mushroom, mushrooms"),
    ("Sweet corn", "Vegetables", "ear-of-corn", 0.69, "1 ct", "One ear, husk on", "corn, corn on the cob"),
    ("Celery", "Vegetables", "leafy-green", 1.99, "1 ct", "One crisp bunch", "celery stalks"),
    ("Eggplant", "Vegetables", "eggplant", 1.99, "per lb", "Glossy purple, for roasting", "aubergine, brinjal, baingan"),
    ("Zucchini", "Vegetables", "cucumber", 1.79, "per lb", "Tender summer squash", "courgette, squash"),
    ("Green beans", "Vegetables", "pea-pod", 2.49, "per lb", "Fresh snap beans", "string beans, beans"),
    ("Cilantro", "Vegetables", "herb", 0.99, "1 ct", "One fresh bunch", "coriander, dhania"),
    # Dairy & eggs
    ("Whole milk", "Dairy & eggs", "glass-of-milk", 3.59, "1 gal", "Rich and creamy, 3.25% milkfat", "milk, full fat milk"),
    ("2% reduced fat milk", "Dairy & eggs", "glass-of-milk", 3.49, "1 gal", "Lighter, same protein", "2% milk, milk, reduced fat"),
    ("Skim milk", "Dairy & eggs", "glass-of-milk", 3.49, "1 gal", "Fat-free milk", "fat free milk, nonfat milk, milk"),
    ("Almond milk", "Dairy & eggs", "glass-of-milk", 3.29, "64 fl oz", "Unsweetened plant milk", "almond, plant milk, dairy free milk"),
    ("Oat milk", "Dairy & eggs", "glass-of-milk", 4.49, "64 fl oz", "Creamy plant milk", "oatmilk, plant milk"),
    ("Large eggs", "Dairy & eggs", "egg", 3.29, "12 ct", "Grade A, the size most recipes use", "eggs, egg, dozen eggs"),
    ("Brown eggs", "Dairy & eggs", "egg", 4.49, "12 ct", "Cage-free brown eggs", "eggs, egg, cage free eggs"),
    ("Salted butter", "Dairy & eggs", "butter", 4.29, "16 oz", "Four sticks to a pound", "butter"),
    ("Unsalted butter", "Dairy & eggs", "butter", 4.29, "16 oz", "Best for baking", "butter, sweet cream butter"),
    ("Sharp cheddar cheese", "Dairy & eggs", "cheese-wedge", 2.99, "8 oz", "Aged, tangy block", "cheddar, cheese"),
    ("Shredded mozzarella", "Dairy & eggs", "cheese-wedge", 2.99, "8 oz", "Melts well on pizza and pasta", "mozzarella, cheese, pizza cheese"),
    ("American cheese slices", "Dairy & eggs", "cheese-wedge", 2.79, "12 oz", "Melty slices for sandwiches", "cheese slices, cheese, singles"),
    ("Cream cheese", "Dairy & eggs", "cheese-wedge", 2.49, "8 oz", "Smooth spread for bagels", "philadelphia, cheese"),
    ("Paneer", "Dairy & eggs", "cheese-wedge", 4.99, "12 oz", "Fresh Indian cheese block", "cottage cheese indian, paneer cheese"),
    ("Greek yogurt", "Dairy & eggs", "bowl-with-spoon", 4.99, "32 oz", "Thick, high-protein, plain", "yogurt, yoghurt, curd, dahi"),
    ("Vanilla yogurt", "Dairy & eggs", "bowl-with-spoon", 2.99, "32 oz", "Smooth and lightly sweet", "yogurt, yoghurt"),
    ("Sour cream", "Dairy & eggs", "bowl-with-spoon", 2.29, "16 oz", "Tangy topping", "sourcream"),
    ("Heavy whipping cream", "Dairy & eggs", "glass-of-milk", 3.99, "16 fl oz", "For whipping and sauces", "heavy cream, cream, whipping cream"),
    ("Coffee creamer", "Dairy & eggs", "glass-of-milk", 4.29, "32 fl oz", "French vanilla creamer", "creamer, half and half"),
    # Meat & seafood
    ("Chicken breast", "Meat & seafood", "poultry-leg", 3.99, "per lb", "Boneless, skinless, lean", "chicken, chicken breasts, boneless chicken"),
    ("Chicken thighs", "Meat & seafood", "poultry-leg", 2.49, "per lb", "Juicy, bone-in", "chicken, thighs"),
    ("Chicken drumsticks", "Meat & seafood", "poultry-leg", 1.69, "per lb", "Budget-friendly, great grilled", "chicken legs, drumstick, chicken"),
    ("Whole chicken", "Meat & seafood", "poultry-leg", 1.49, "per lb", "Whole fryer, about 5 lb", "chicken, roaster"),
    ("Ground beef 80/20", "Meat & seafood", "cut-of-meat", 5.49, "per lb", "Juicy blend for burgers", "ground beef, mince, minced meat, hamburger meat, beef"),
    ("Ground turkey", "Meat & seafood", "cut-of-meat", 4.49, "16 oz", "Lean 93/7", "turkey, ground meat"),
    ("Ribeye steak", "Meat & seafood", "cut-of-meat", 13.99, "per lb", "Rich, marbled steak", "steak, beef steak, rib eye"),
    ("Pork chops", "Meat & seafood", "cut-of-meat", 3.99, "per lb", "Bone-in center cut", "pork, chops"),
    ("Bacon", "Meat & seafood", "bacon", 5.99, "16 oz", "Hickory-smoked strips", "bacon strips"),
    ("Sliced turkey breast", "Meat & seafood", "sandwich", 4.99, "9 oz", "Deli-style sandwich meat", "turkey slices, deli meat, lunch meat"),
    ("Hot dogs", "Meat & seafood", "hot-dog", 4.49, "8 ct", "Beef franks", "franks, hotdogs, sausages"),
    ("Atlantic salmon fillet", "Meat & seafood", "fish", 9.99, "per lb", "Fresh, skin-on fillet", "salmon, fish"),
    ("Tilapia fillets", "Meat & seafood", "fish", 6.99, "per lb", "Mild white fish", "tilapia, fish"),
    ("Raw shrimp", "Meat & seafood", "shrimp", 9.99, "2 lb bag", "Frozen, peeled and deveined", "shrimp, prawns, prawn"),
    ("Crab meat", "Meat & seafood", "crab", 8.99, "8 oz", "Maryland-style lump crab", "crab, blue crab, lump crab"),
    ("Firm tofu", "Meat & seafood", "cheese-wedge", 2.29, "14 oz", "Plant protein, holds its shape", "tofu, bean curd"),
    # Bakery
    ("White bread", "Bakery", "bread", 2.19, "20 oz", "Soft sandwich loaf", "bread, sandwich bread, loaf"),
    ("Whole wheat bread", "Bakery", "bread", 2.79, "20 oz", "100% whole wheat loaf", "wheat bread, brown bread, bread"),
    ("Bagels", "Bakery", "bagel", 3.49, "6 ct", "Plain New York-style", "bagel"),
    ("Croissants", "Bakery", "croissant", 4.99, "6 ct", "Buttery and flaky", "croissant"),
    ("French baguette", "Bakery", "baguette-bread", 2.49, "1 ct", "Crusty, baked daily", "baguette, french bread"),
    ("Flour tortillas", "Bakery", "flatbread", 2.99, "10 ct", "Soft taco-size", "tortillas, wraps, tortilla"),
    ("Naan", "Bakery", "flatbread", 3.99, "4 ct", "Soft Indian flatbread", "naan bread, flatbread"),
    ("Hamburger buns", "Bakery", "hamburger", 2.29, "8 ct", "Soft sesame buns", "buns, burger buns"),
    ("Chocolate chip cookies", "Bakery", "cookie", 3.99, "13 oz", "Crispy classic cookies", "cookies, cookie"),
    ("Donuts", "Bakery", "doughnut", 5.99, "6 ct", "Glazed ring donuts", "doughnuts, donut"),
    # Pantry
    ("Long grain white rice", "Pantry", "cooked-rice", 3.29, "5 lb", "Fluffy, separate grains", "rice, white rice"),
    ("Basmati rice", "Pantry", "cooked-rice", 9.99, "10 lb", "Fragrant long-grain rice", "rice, basmati, chawal"),
    ("Brown rice", "Pantry", "cooked-rice", 2.99, "2 lb", "Whole-grain rice", "rice"),
    ("Spaghetti", "Pantry", "spaghetti", 1.39, "16 oz", "Dry pasta, serves 4 to 6", "pasta, noodles"),
    ("Penne pasta", "Pantry", "spaghetti", 1.39, "16 oz", "Tube pasta for baked dishes", "pasta, penne"),
    ("Macaroni and cheese", "Pantry", "cheese-wedge", 1.19, "7.25 oz", "Boxed mac and cheese", "mac and cheese, mac n cheese, kraft dinner"),
    ("Ramen noodles", "Pantry", "steaming-bowl", 3.49, "12 ct", "Instant noodle packs", "ramen, instant noodles, maggi, noodles"),
    ("Pasta sauce", "Pantry", "jar", 2.49, "24 oz", "Tomato basil marinara", "marinara, spaghetti sauce, tomato sauce"),
    ("Canned diced tomatoes", "Pantry", "canned-food", 1.29, "14.5 oz", "For sauces, soups and curries", "diced tomatoes, canned tomatoes"),
    ("Black beans", "Pantry", "canned-food", 0.99, "15 oz", "Canned, ready to heat", "beans, canned beans"),
    ("Chickpeas", "Pantry", "beans", 1.19, "15 oz", "Canned garbanzo beans", "garbanzo, chana, chick peas"),
    ("Red lentils", "Pantry", "beans", 2.99, "2 lb", "Quick-cooking dal", "lentils, dal, daal, masoor"),
    ("Chicken noodle soup", "Pantry", "canned-food", 1.79, "10.75 oz", "Classic canned soup", "soup, canned soup"),
    ("Tuna", "Pantry", "canned-food", 1.29, "5 oz", "Chunk light in water", "canned tuna, tuna fish"),
    ("Peanut butter", "Pantry", "peanuts", 3.49, "16 oz", "Creamy, no-stir", "peanut, pb"),
    ("Strawberry jam", "Pantry", "jar", 3.29, "18 oz", "Sweet fruit spread", "jam, jelly, preserves"),
    ("Honey", "Pantry", "honey-pot", 5.99, "12 oz", "Pure clover honey", "honey bear"),
    ("Maple syrup", "Pantry", "pancakes", 8.99, "12.5 fl oz", "100% pure maple", "syrup, pancake syrup"),
    ("All-purpose flour", "Pantry", "bread", 3.29, "5 lb", "For baking and breading", "flour, maida, atta"),
    ("Granulated sugar", "Pantry", "salt", 3.99, "4 lb", "Pure cane sugar", "sugar, white sugar"),
    ("Table salt", "Pantry", "salt", 1.19, "26 oz", "Iodized salt", "salt"),
    ("Black pepper", "Pantry", "salt", 3.99, "3 oz", "Ground black pepper", "pepper, kali mirch"),
    ("Vegetable oil", "Pantry", "lotion-bottle", 4.49, "48 fl oz", "Neutral oil for frying", "oil, cooking oil, canola oil"),
    ("Olive oil", "Pantry", "olive", 9.99, "25.5 fl oz", "Extra virgin", "evoo, oil"),
    ("Ketchup", "Pantry", "french-fries", 3.49, "32 oz", "Tomato ketchup", "catsup, tomato ketchup"),
    ("Mayonnaise", "Pantry", "jar", 4.49, "30 fl oz", "Creamy real mayo", "mayo"),
    ("Old Bay seasoning", "Pantry", "salt", 4.99, "6 oz", "Maryland's seafood spice", "old bay, seafood seasoning"),
    ("Oatmeal", "Pantry", "bowl-with-spoon", 4.49, "42 oz", "Old-fashioned rolled oats", "oats, rolled oats, porridge"),
    ("Corn flakes cereal", "Pantry", "bowl-with-spoon", 3.99, "18 oz", "Crispy breakfast cereal", "cereal, cornflakes"),
    ("Pancake mix", "Pantry", "pancakes", 3.29, "32 oz", "Just add water", "pancake, waffle mix"),
    # Snacks
    ("Potato chips", "Snacks", "french-fries", 4.29, "8 oz", "Classic salted chips", "chips, crisps"),
    ("Tortilla chips", "Snacks", "taco", 3.99, "13 oz", "Restaurant-style chips", "nachos, chips"),
    ("Popcorn", "Snacks", "popcorn", 4.49, "6 ct", "Microwave butter popcorn", "microwave popcorn"),
    ("Pretzels", "Snacks", "pretzel", 3.29, "16 oz", "Crunchy mini twists", "pretzel"),
    ("Salted peanuts", "Snacks", "peanuts", 3.49, "16 oz", "Dry-roasted peanuts", "peanuts, nuts"),
    ("Mixed nuts", "Snacks", "chestnut", 7.99, "15 oz", "Lightly salted mix", "nuts, cashews, almonds"),
    ("Milk chocolate bar", "Snacks", "chocolate-bar", 1.79, "1.55 oz", "Classic chocolate bar", "chocolate, candy bar"),
    ("Gummy candy", "Snacks", "candy", 2.99, "10 oz", "Fruity gummy bears", "candy, gummies, gummy bears"),
    ("Granola bars", "Snacks", "cookie", 3.99, "12 ct", "Chewy oat bars", "granola, snack bars"),
    ("Crackers", "Snacks", "rice-cracker", 3.49, "13.7 oz", "Buttery round crackers", "cracker, saltines"),
    # Drinks
    ("Orange juice", "Drinks", "beverage-box", 3.99, "52 fl oz", "100% juice, no pulp", "oj, juice"),
    ("Apple juice", "Drinks", "beverage-box", 2.99, "64 fl oz", "100% apple juice", "juice"),
    ("Bottled water", "Drinks", "droplet", 4.99, "24 ct", "16.9 oz bottles", "water, water bottles"),
    ("Sparkling water", "Drinks", "droplet", 4.99, "8 ct", "Unflavored seltzer cans", "seltzer, soda water, club soda"),
    ("Cola", "Drinks", "cup-with-straw", 7.99, "12 ct", "12 oz cans", "soda, coke, pop, soft drink"),
    ("Ground coffee", "Drinks", "hot-beverage", 8.99, "12 oz", "Medium roast for drip", "coffee"),
    ("Coffee pods", "Drinks", "hot-beverage", 9.99, "12 ct", "Single-serve medium roast", "k cups, kcups, coffee"),
    ("Black tea bags", "Drinks", "teapot", 3.49, "100 ct", "Classic black tea", "tea, chai, tea bags"),
    ("Sports drink", "Drinks", "cup-with-straw", 1.29, "28 fl oz", "Electrolyte drink", "gatorade, powerade"),
    # Frozen
    ("Frozen pizza", "Frozen", "pizza", 5.49, "1 ct", "Pepperoni, 12-inch", "pizza"),
    ("Vanilla ice cream", "Frozen", "ice-cream", 4.99, "48 fl oz", "Classic vanilla", "ice cream, icecream"),
    ("Frozen mixed vegetables", "Frozen", "pea-pod", 1.49, "16 oz", "Peas, carrots, corn, beans", "frozen veggies, mixed veg"),
    ("Frozen peas", "Frozen", "pea-pod", 1.29, "16 oz", "Sweet green peas", "peas, matar"),
    ("Frozen french fries", "Frozen", "french-fries", 3.49, "32 oz", "Crinkle-cut fries", "fries, french fries"),
    ("Frozen waffles", "Frozen", "waffle", 2.99, "10 ct", "Toaster waffles", "waffles, eggo"),
    ("Frozen dumplings", "Frozen", "dumpling", 6.99, "24 oz", "Pork and chive potstickers", "dumplings, potstickers, momos, gyoza"),
    ("Ice", "Frozen", "ice", 2.99, "10 lb", "Bag of ice cubes", "ice cubes"),
    # Household
    ("Paper towels", "Household", "roll-of-paper", 9.99, "6 ct", "Six double rolls", "kitchen towels, paper towel"),
    ("Toilet paper", "Household", "roll-of-paper", 9.99, "12 ct", "Twelve double rolls", "tp, bath tissue, tissue"),
    ("Dish soap", "Household", "bubbles", 3.49, "28 fl oz", "Grease-cutting liquid", "dishwashing liquid, dish liquid"),
    ("Laundry detergent", "Household", "bubbles", 11.99, "92 fl oz", "Liquid, about 64 loads", "detergent, washing liquid, tide"),
    ("Trash bags", "Household", "wastebasket", 8.99, "40 ct", "13 gallon kitchen bags", "garbage bags, bin bags"),
    ("Sponges", "Household", "sponge", 3.49, "6 ct", "Scrub sponges", "sponge, scrubber"),
    ("Aluminum foil", "Household", "roll-of-paper", 4.49, "75 sq ft", "Standard kitchen foil", "foil, tin foil"),
    # Personal care & baby & pet
    ("Bar soap", "Personal care", "soap", 4.99, "8 ct", "Moisturizing bars", "soap, bath soap"),
    ("Shampoo", "Personal care", "lotion-bottle", 5.99, "25 fl oz", "Daily shampoo", "hair wash"),
    ("Toothpaste", "Personal care", "toothbrush", 3.49, "5 oz", "Fluoride toothpaste", "tooth paste, colgate"),
    ("Toothbrushes", "Personal care", "toothbrush", 3.99, "4 ct", "Soft bristles", "toothbrush"),
    ("Hand lotion", "Personal care", "lotion-bottle", 5.49, "16 fl oz", "Daily moisturizer", "lotion, moisturizer"),
    ("Baby wipes", "Baby & pet", "baby-bottle", 3.49, "72 ct", "Unscented, sensitive", "wipes"),
    ("Diapers", "Baby & pet", "baby-bottle", 24.99, "120 ct", "Size 3 jumbo pack", "nappies, diaper"),
    ("Dry dog food", "Baby & pet", "bone", 14.99, "15 lb", "Chicken and rice formula", "dog food, pet food"),
    ("Cat food", "Baby & pet", "paw-prints", 9.99, "12 ct", "Wet food, 3 oz cans", "cat food cans, pet food"),
]

STORES = ["Aldi", "Walmart", "Amazon Fresh", "Giant", "Harris Teeter"]
# Rough price level per store, only used to make sample prices plausible.
INDEX = {"Aldi": 0.86, "Walmart": 0.92, "Amazon Fresh": 1.0, "Giant": 1.06, "Harris Teeter": 1.12}


def _h(*parts: str) -> int:
    return int(hashlib.sha256("|".join(parts).encode()).hexdigest()[:8], 16)


def stores_for(name: str) -> list[str]:
    """Not every store stocks everything; keep at least three per item, stable across builds."""
    keep = [s for s in STORES if _h(name, s, "stock") % 100 < 88]
    for s in STORES:
        if len(keep) >= 3:
            break
        if s not in keep:
            keep.append(s)
    return [s for s in STORES if s in keep]


def build() -> dict:
    sys.path.insert(0, str(ROOT))
    from app.adapters.linkouts import search_url

    items = []
    for name, cat, icon, price, size, desc, aliases in ITEMS:
        term = name.lower().replace("jalapeño", "jalapeno")
        items.append({
            "id": term.replace(" ", "-").replace("/", "-").replace("%", "pct").replace("'", ""),
            "name": name,
            "category": cat,
            "icon": f"icons/{icon}.svg",
            "price": price,
            "size": size,
            "description": desc,
            "aliases": [a.strip() for a in aliases.split(",") if a.strip()],
            "stores": stores_for(name),
            "links": {s: search_url(s, term) for s in STORES},
        })
    return {"stores": STORES, "index": INDEX, "items": items}


def copy_icons(items: list[dict]) -> None:
    pkg = ROOT.parent / "node_modules"
    candidates = [Path(p) for p in sys.argv[1:]] + [pkg, Path("/tmp/claude-0/emoji/node_modules")]
    src = next((c / "@iconify-json/fluent-emoji/icons.json" for c in candidates
                if (c / "@iconify-json/fluent-emoji/icons.json").exists()), None)
    if not src:
        print("icons: @iconify-json/fluent-emoji not found (npm i @iconify-json/fluent-emoji); skipped")
        return
    data = json.loads(src.read_text())
    out = ROOT / "docs" / "icons"
    out.mkdir(exist_ok=True)
    w, h = data.get("width", 32), data.get("height", 32)
    for name in sorted({Path(i["icon"]).stem for i in items} | {"basket", "shopping-cart"}):
        icon = data["icons"][name]
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {icon.get("width", w)} {icon.get("height", h)}">'
               f'{icon["body"]}</svg>')
        (out / f"{name}.svg").write_text(svg)
    (out / "LICENSE.txt").write_text(
        "Icons: Fluent Emoji by Microsoft, https://github.com/microsoft/fluentui-emoji\nMIT License, Copyright (c) Microsoft Corporation.\n")
    print("icons:", len(list(out.glob("*.svg"))))


if __name__ == "__main__":
    catalog = build()
    copy_icons(catalog["items"])
    (ROOT / "docs" / "catalog.json").write_text(json.dumps(catalog, separators=(",", ":")))
    print("items:", len(catalog["items"]))
