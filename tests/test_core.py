import pytest
from fastapi.testclient import TestClient

from app.compare import price_basket, rank, relevant
from app.models import Offer
from app.units import parse_size, unit_price


@pytest.mark.parametrize("text,qty,dim", [
    ("2 lb bag", 32, "weight"),
    ("16 oz", 16, "weight"),
    ("52 fl oz", 52, "volume"),
    ("1 gal", 128, "volume"),
    ("12 ct", 12, "count"),
    ("1 dozen", 12, "count"),
    ("6 x 12 fl oz", 72, "volume"),
    ("per lb", 16, "weight"),
    ("$2.99/lb", 16, "weight"),
    ("1/2 gal", 64, "volume"),
])
def test_parse_size(text, qty, dim):
    s = parse_size(text)
    assert s is not None and s.dimension == dim and s.quantity == pytest.approx(qty, rel=1e-3)


def test_unparseable_size():
    assert parse_size("family pack") is None


def test_unit_price_per_lb():
    up, unit = unit_price(5.00, parse_size("2 lb"))
    assert (up, unit) == (2.5, "lb")


def _o(retailer, title, price, size):
    return Offer(retailer=retailer, title=title, price=price, size=size, url="https://x").with_unit_price()


def test_rank_uses_unit_price_not_sticker_price():
    small = _o("A", "Grapes", 2.99, "1 lb")      # $2.99/lb
    big = _o("B", "Grapes", 4.98, "2 lb bag")    # $2.49/lb — higher sticker, cheaper per lb
    assert rank([small, big])[0].retailer == "B"


def test_relevant_filters_unrelated():
    keep = _o("A", "Red Seedless Grapes", 3, "1 lb")
    drop = _o("A", "Bananas", 1, "1 lb")
    assert relevant([keep, drop], "grapes") == [keep]


def test_basket_split_and_single_store():
    lines = [
        ("milk", 1, [_o("A", "Milk", 3.00, "1 gal"), _o("B", "Milk", 4.00, "1 gal")]),
        ("eggs", 2, [_o("A", "Eggs", 4.00, "12 ct"), _o("B", "Eggs", 3.00, "12 ct")]),
    ]
    r = price_basket(lines)
    totals = {s["retailer"]: s["total"] for s in r["stores"]}
    assert totals == {"A": 11.0, "B": 10.0}
    assert r["best_single_store"] == "B"
    assert r["split"]["total"] == 9.0 and r["savings_vs_best_single"] == 1.0


def test_smaller_pack_cannot_win_basket_by_being_small():
    lines = [("milk", 1, [_o("A", "Milk", 4.00, "1 gal"), _o("B", "Milk", 2.50, "0.5 gal"),
                          _o("C", "Milk", 4.20, "1 gal")])]
    r = price_basket(lines)
    totals = {s["retailer"]: s["total"] for s in r["stores"]}
    assert totals["B"] == 5.0 and r["best_single_store"] == "A"
    assert r["split"]["items"][0]["amount"] == "1 gal"


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setenv("DEMO_MODE", "on")
    import importlib
    import app.config, app.main
    importlib.reload(app.config)
    importlib.reload(app.main)
    return TestClient(app.main.app)


def test_search_demo(client):
    r = client.get("/api/search", params={"q": "grapes", "zip": "21218"})
    assert r.status_code == 200
    body = r.json()
    assert body["demo_mode"] is True
    assert {o["retailer"] for o in body["offers"]} >= {"Giant", "Walmart", "Amazon Fresh"}
    assert all(o["source"] == "demo" for o in body["offers"])
    ups = [o["unit_price"] for o in body["offers"] if o["unit"] == "lb"]
    assert ups == sorted(ups)


def test_rejects_non_maryland_zip(client):
    assert client.get("/api/search", params={"q": "milk", "zip": "10001"}).status_code == 400


def test_basket_and_order(client):
    items = {"zip": "21218", "items": [{"query": "milk", "quantity": 1}, {"query": "eggs", "quantity": 2}]}
    r = client.post("/api/basket", json=items).json()
    assert r["best_single_store"] and r["split"]["total"] > 0
    o = client.post("/api/order/instacart", json=items).json()
    assert o["url"].startswith("https://www.instacart.com")


def test_typo_correction_and_catalog_search():
    from app.catalog import correct, find
    assert correct("graps") == "grapes"
    assert correct("bananna") == "banana"
    assert find("chiken")[0]["name"] == "Chicken breast"
    assert find("milk")[0]["name"] == "Whole milk"
    assert find("toilet paper")[0]["name"] == "Toilet paper"
    assert len(__import__("app.catalog", fromlist=["catalog"]).catalog()["items"]) >= 150


def test_search_typo_through_api(client):
    body = client.get("/api/search", params={"q": "graps", "zip": "21218"}).json()
    assert body["offers"] and "grapes" in body["offers"][0]["title"].lower()
    assert body["guide"]["icon"].startswith("icons/")


def test_store_links_use_verified_formats():
    from app.adapters.linkouts import search_url
    assert search_url("Harris Teeter", "grapes").endswith("searchType=default_search")
    assert search_url("Aldi", "grapes") == "https://www.aldi.us/store/aldi/s?k=grapes"
    assert search_url("Walmart", "red grapes") == "https://www.walmart.com/search?q=red+grapes"
