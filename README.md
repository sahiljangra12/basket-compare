# Basket Compare

**Live demo: https://sahiljangra12.github.io/basket-compare/** (runs in the browser with sample prices)

Compare grocery prices across Maryland stores, see which store is cheapest for your whole list, and go straight to ordering.

- **Search 168 everyday groceries** with suggestions as you type. Typos are fine: "graps", "chiken", "bananna" and "brocoli" all find the right item, and aliases work too ("curd", "aloo", "tp").
- **Compare every store** for an item, ranked by unit price, with a one-tap order button that opens that store's page for the item.
- **Basket**: add items to see the whole list's total at each store, and how much you'd save by splitting between two.
- Illustrated product icons (Fluent Emoji by Microsoft, MIT licence).

## Run it

```bash
cd basket-compare
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # add keys as you get them
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000. With no keys, the app shows a **sample prices** notice and uses made-up numbers so you can work on the interface. Run the tests with `pytest -q`.

## Two ways it runs

- **With the Python server** (`uvicorn app.main:app`): the page calls `/api/...` and gets real prices from whichever retailer keys you've set.
- **On GitHub Pages**: there's no server, so `docs/engine.js` runs the same unit-price and basket maths in the browser on sample prices. Real prices need the server deployed somewhere (Render, Railway, Fly.io), because API keys can't live in a public web page.

## Where real prices come from

| Retailer | Source | Prices | Ordering | Cost |
|---|---|---|---|---|
| Harris Teeter (Kroger family) | Kroger Public API | Store shelf price near the ZIP | Product page link | Free, self-service (10,000 product calls/day) |
| Walmart | Walmart Affiliate API | Walmart.com online price (national) | Affiliate product link (earns commission) | Free developer account |
| Giant, Aldi, Safeway, ... | Instacart Developer Platform | Not available (no price endpoint) | Instacart shopping-list page | Free, self-service keys |
| Amazon Fresh | Amazon Creators API | Opens after 10 referred sales in 30 days | Search link with your Associates tag | Free once eligible |

Getting keys, in order of value:
1. **Kroger** — developer.kroger.com. Takes minutes. First real store prices.
2. **Instacart** — Developer Platform dashboard. Makes "Order whole basket" create a real list.
3. **Walmart** — walmart.io. Needs an RSA key pair: `openssl genrsa -out keys/walmart_private_key.pem 2048` then upload the public key.
4. **Amazon Associates** — sign up now so the tag earns on Fresh links; the price API unlocks after qualifying sales.

## Project layout

```
app/
  main.py          API routes + serves the web page
  adapters/        one file per price source (kroger, walmart, instacart, demo, linkouts)
  units.py         size parsing ("2 lb bag", "52 fl oz") and unit prices
  compare.py       relevance filter, ranking, basket pricing
  cache.py         SQLite price cache
  catalog.py       shared product catalog + typo correction
docs/              the web page — also served by GitHub Pages
  catalog.json     168 products (built by scripts/build_catalog.py)
  engine.js        search, unit prices and basket maths in the browser
  icons/           product illustrations (Fluent Emoji, MIT)
tests/             pytest suite
```

Adding a retailer = one new file in `app/adapters/` with a `search(query, zip)` method, then add it to `LIVE_SOURCES` in `main.py`.

## Known gaps (the roadmap)

- **Giant has no price data yet.** Options: a Giant/Ahold partnership, a licensed data vendor, or Instacart's Partner API (in-app catalog + checkout, by application). Scraping Giant's site breaks its terms of service — avoid it for a public launch.
- **Order links open each store's search results for the item** until that store's API is connected; live Kroger and Walmart results link to the exact product page. Giant and Amazon block automated checks, so their link formats couldn't be tested.
- **Product matching across stores is by name.** Next: match by UPC so the same exact product lines up across retailers.
- **Walmart prices are national online prices**, not a specific store's shelf price; the app labels them "Online price".
- **Prices refresh on demand with a cache**, not continuously. For a launch, add a scheduled job that pre-fetches the top ~500 staples per ZIP.
- **Not yet a phone app.** The page works on phones; wrap it with Capacitor or rebuild in React Native for the App Store / Play Store.
