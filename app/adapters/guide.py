"""Product guide: a photo, a short description and a buying tip for each sample item.

Photos are from Wikimedia Commons under the licenses listed (credited in the UI and in
docs/credits.html). They show the kind of product, not a specific store's package; live
retailer results use the retailer's own product photo instead.
"""
from __future__ import annotations

from urllib.parse import quote

_THUMB = "https://upload.wikimedia.org/wikipedia/commons/thumb/{a}/{ab}/{name}/500px-{name}"


def _photo(path: str, file: str, author: str, license: str) -> dict:
    a, ab = path.split("/")
    name = quote(file.replace(" ", "_"))
    return {
        "src": _THUMB.format(a=a, ab=ab, name=name),
        "page": "https://commons.wikimedia.org/wiki/File:" + name,
        "author": author,
        "license": license,
    }


GUIDE: dict[str, dict] = {
    "Red Seedless Grapes": {
        "photo": _photo("d/d0", "Red grapes (1).jpg", "Scott Bauer, USDA", "Public domain"),
        "description": "Crisp, sweet table grapes with no seeds. Good for snacking, lunchboxes and freezing.",
        "tip": "Pick bunches with green, flexible stems; brown brittle stems mean older fruit.",
    },
    "Green Seedless Grapes": {
        "photo": _photo("b/b6", "A bunch of grapes.jpg", "Vijay Kumar Soren", "CC BY-SA 4.0"),
        "description": "Tart-sweet and firm, a little sharper than red grapes.",
        "tip": "A slight yellow tint means riper and sweeter.",
    },
    "Bananas": {
        "photo": _photo("d/d1", "Banana bunch.jpeg", "NW Indian Language Institute", "CC BY 3.0"),
        "description": "Sold by the pound, usually around three bananas to a pound.",
        "tip": "Buy a mix of yellow and green so they don't all ripen on the same day.",
    },
    "Gala Apples": {
        "photo": _photo("e/e9", "A Gala Apple.jpg", "Corn cheese", "CC BY-SA 4.0"),
        "description": "Mild, sweet and crunchy. One of the cheapest everyday apples.",
        "tip": "Bagged apples usually cost less per pound than loose ones.",
    },
    "Strawberries": {
        "photo": _photo("1/1b", "Liat Portal for Foodie Disorder - Fresh Strawberries.jpg", "HaJunkiyada", "CC BY-SA 4.0"),
        "description": "Usually sold in 1 lb clamshells. Best eaten within two or three days.",
        "tip": "Check the bottom of the box for crushed or moldy berries.",
    },
    "Whole Milk": {
        "photo": _photo("a/a8", "Milk Pitcher With Lid.jpg", "Pitcherman (Zenon Niewada)", "Public domain"),
        "description": "About 3.25% milkfat. A gallon is roughly 16 cups.",
        "tip": "Grab a jug from the back of the case for the latest sell-by date.",
    },
    "2% Reduced Fat Milk": {
        "photo": _photo("8/87", "Milk jug top.png", "Kelapstick", "Public domain"),
        "description": "Lighter than whole milk with the same protein and calcium.",
        "tip": "Half gallons often cost more per ounce than a full gallon.",
    },
    "Large Grade A Eggs": {
        "photo": _photo("9/92", "Brown eggs in a deviled egg plate.jpg", "E4024", "CC BY-SA 4.0"),
        "description": "The standard size most recipes assume. Brown and white eggs taste the same.",
        "tip": "Open the carton and check for cracked shells before you buy.",
    },
    "White Sandwich Bread": {
        "photo": _photo("7/77", "Tin Loaf - one slash in the crust.jpg", "Mike Finn", "CC BY 2.0"),
        "description": "Soft sliced loaf, typically 20 oz and about 22 slices.",
        "tip": "Freeze half the loaf if you won't finish it within five days.",
    },
    "Boneless Skinless Chicken Breast": {
        "photo": _photo("b/b8", "Raw chicken slices.jpg", "kakyusei", "CC0"),
        "description": "Lean, quick-cooking cut. Family packs cut the price per pound.",
        "tip": "Family packs freeze well when split into meal-size bags.",
    },
    "80% Lean Ground Beef": {
        "photo": _photo("6/65", "Hakket-oksekoed.jpg", "Gajda-13", "CC BY-SA 3.0"),
        "description": "Juicy blend for burgers and meatballs. 80/20 means 20% fat.",
        "tip": "Use it within two days of buying, or freeze it flat.",
    },
    "Long Grain White Rice": {
        "photo": _photo("6/6e", "Uncooked ST25 rice on bamboo surface.jpg", "VinhNguyen.1257", "CC BY-SA 4.0"),
        "description": "Fluffy, separate grains. One pound makes about ten cooked cups.",
        "tip": "Bigger bags are much cheaper per pound and keep for months.",
    },
    "Spaghetti Pasta": {
        "photo": _photo("d/d4", "Spaghetti measure macro.jpg", "Bodhi Peace", "CC BY-SA 4.0"),
        "description": "Dry durum-wheat pasta. A 1 lb box serves four to six.",
        "tip": "Store brands are often made by the same mills as name brands.",
    },
    "Sharp Cheddar Cheese": {
        "photo": _photo("1/18", "Somerset-Cheddar.jpg", "J.P.Lon", "CC BY-SA 3.0"),
        "description": "Aged cheddar with a stronger, tangier flavor than mild.",
        "tip": "Blocks cost less per ounce than pre-shredded bags.",
    },
    "Salted Butter": {
        "photo": _photo("1/1f", "2019-11-28 14 27 10 A stick of butter laid out for Thanksgiving Dinner in the Parkway Village section of Ewing Township, Mercer County, New Jersey.jpg", "Famartin", "CC BY-SA 4.0"),
        "description": "Usually four 4 oz sticks to a 1 lb box.",
        "tip": "Butter freezes for months, so stock up when it's on sale.",
    },
    "Orange Juice, No Pulp": {
        "photo": _photo("6/67", "Orange juice 1 edit1.jpg", "USDA", "Public domain"),
        "description": "100% juice, pulp strained out. Chilled cartons beat concentrate on taste.",
        "tip": "Compare per fluid ounce; carton sizes vary between 52 and 89 oz.",
    },
    "Greek Yogurt, Plain": {
        "photo": _photo("6/6c", "Yogurt, fruit, granola bowl (34999358091).jpg", "T.Tseng", "CC BY 2.0"),
        "description": "Strained yogurt, thick and high in protein. Plain has no added sugar.",
        "tip": "The 32 oz tub is usually far cheaper than single cups.",
    },
    "Roma Tomatoes": {
        "photo": _photo("5/5f", "Roma or Bangalore Tomatoes (Indian hybrid).jpg", "Aravind Sivaraj", "CC BY-SA 3.0"),
        "description": "Meaty plum tomatoes with fewer seeds, good for sauces and salsa.",
        "tip": "Keep them on the counter, not in the fridge, for better flavor.",
    },
    "Yellow Onions": {
        "photo": _photo("2/25", "Onion on White.JPG", "Colin", "CC BY-SA 3.0"),
        "description": "All-purpose cooking onion that turns sweet when cooked.",
        "tip": "Choose firm onions with dry, papery skins and no soft spots.",
    },
    "Russet Potatoes": {
        "photo": _photo("d/de", "Russet potato.jpg", "Steve Caruso", "CC BY-SA 2.5"),
        "description": "Starchy potatoes for baking, mashing and fries.",
        "tip": "Store somewhere cool and dark, away from onions.",
    },
    "Ground Coffee, Medium Roast": {
        "photo": _photo("8/8b", "Coarsely grounded coffee beans in white bowl with intact roasted bean.png", "Alorin", "CC BY 4.0"),
        "description": "Balanced, everyday roast for drip machines.",
        "tip": "Bag sizes shrink quietly (12 oz to 11.3 oz), so compare per ounce.",
    },
}
