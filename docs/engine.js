// Browser-only price engine, used when no Basket Compare server is reachable
// (for example on GitHub Pages). It mirrors app/units.py, app/compare.py and the
// sample data in app/adapters/demo.py. Prices here are SAMPLE prices.

const UNITS = {
  "fl oz": ["volume", 1], "floz": ["volume", 1], "fluid ounces": ["volume", 1],
  gal: ["volume", 128], gallon: ["volume", 128], qt: ["volume", 32], pt: ["volume", 16],
  l: ["volume", 33.814], ml: ["volume", 0.033814],
  lbs: ["weight", 16], lb: ["weight", 16], pound: ["weight", 16], pounds: ["weight", 16],
  oz: ["weight", 1], ounces: ["weight", 1], kg: ["weight", 35.274], g: ["weight", 0.035274],
  ct: ["count", 1], count: ["count", 1], each: ["count", 1], pack: ["count", 1], dozen: ["count", 12],
};
const UNIT_RE = Object.keys(UNITS).sort((a, b) => b.length - a.length).map((u) => u.replace(" ", "\\s")).join("|");
const NUM = "(\\d+(?:\\.\\d+)?|\\d+/\\d+)";
const MULTI = new RegExp(`${NUM}\\s*(?:x|×)\\s*${NUM}\\s*(${UNIT_RE})\\b`, "i");
const SINGLE = new RegExp(`${NUM}\\s*-?\\s*(${UNIT_RE})\\b`, "i");
const PER = new RegExp(`(?:/|per\\s+)(${UNIT_RE})\\b`, "i");
const DISPLAY = { weight: ["lb", 16], volume: ["fl oz", 1], count: ["item", 1] };
const DISPLAY_PER = { lb: 16, "fl oz": 1, item: 1 };

const num = (t) => (t.includes("/") ? t.split("/")[0] / t.split("/")[1] : parseFloat(t));
const unitOf = (u) => UNITS[u.toLowerCase().replace(/\s+/, " ")];

export function parseSize(text) {
  if (!text) return null;
  const t = text.toLowerCase();
  let m = t.match(MULTI);
  if (m) { const [dim, k] = unitOf(m[3]); return { qty: num(m[1]) * num(m[2]) * k, dim }; }
  m = t.match(SINGLE);
  if (m) { const [dim, k] = unitOf(m[2]); return { qty: num(m[1]) * k, dim }; }
  m = t.match(PER);
  if (m) { const [dim, k] = unitOf(m[1]); return { qty: k, dim }; }
  return null;
}

function withUnitPrice(o) {
  const s = parseSize(o.size) || parseSize(o.title);
  if (s) {
    const [label, per] = DISPLAY[s.dim];
    o.unit = label;
    o.unit_price = Math.round((o.price / (s.qty / per)) * 10000) / 10000;
  }
  return o;
}

function noise(...parts) {
  let h = 2166136261;
  for (const ch of parts.join("|")) { h ^= ch.charCodeAt(0); h = Math.imul(h, 16777619); }
  return 0.9 + ((h >>> 0) % 2000) / 10000;
}

let catalog;
async function loadCatalog() {
  if (!catalog) catalog = await (await fetch("sample-catalog.json?v=4")).json();
  return catalog;
}

const STOP = new Set(["the", "a", "an", "of", "and", "fresh", "organic"]);
const tokens = (t) => new Set((t.toLowerCase().match(/[a-z0-9%]+/g) || [])
  .filter((w) => !STOP.has(w)).map((w) => (w.length > 3 ? w.replace(/s+$/, "") : w)));

function mainUnit(offers) {
  const c = {};
  offers.forEach((o) => o.unit && (c[o.unit] = (c[o.unit] || 0) + 1));
  return Object.entries(c).sort((a, b) => b[1] - a[1])[0]?.[0] ?? null;
}

function rank(offers) {
  const unit = mainUnit(offers);
  const comp = offers.filter((o) => o.unit === unit && o.unit_price != null)
    .sort((a, b) => a.unit_price - b.unit_price || a.price - b.price);
  const rest = offers.filter((o) => !comp.includes(o)).sort((a, b) => a.price - b.price);
  return [...comp, ...rest];
}

const UNPRICED_NOTE = {
  Giant: "No public price API — check price on Giant's site or order through Instacart.",
  "Amazon Fresh": "Amazon's product API opens after the affiliate account has qualifying sales.",
  Aldi: "No public price API — order through Instacart.",
};

async function findOffers(query, zip) {
  const cat = await loadCatalog();
  const q = query.toLowerCase().trim();
  const offers = [];
  for (const item of cat.items) {
    if (!item.keywords.some((k) => k.includes(q) || q.includes(k)) && !item.title.toLowerCase().includes(q)) continue;
    const ref = parseSize(Object.values(item.sizes)[0]);
    const perBase = item.base / ref.qty;
    for (const [retailer, size] of Object.entries(item.sizes)) {
      const qty = parseSize(size).qty;
      let price = perBase * qty * cat.index[retailer] * noise(item.title, retailer, zip);
      if (qty > 1.5 * ref.qty) price *= 0.93;
      offers.push(withUnitPrice({
        retailer, title: item.title, size, price: Math.max(Math.round(price * 100) / 100, 0.25),
        url: item.urls[retailer], in_stock: true, source: "demo",
        image: item.guide?.photo.src ?? null, description: item.guide?.description ?? null,
        store: ["Giant", "Harris Teeter", "Aldi"].includes(retailer) ? `${retailer} — sample store` : null,
        price_scope: ["Walmart", "Amazon Fresh"].includes(retailer) ? "online" : "store",
      }));
    }
  }
  const need = tokens(query);
  const rel = offers.filter((o) => [...need].every((w) => tokens(o.title).has(w)));
  return rank(rel.length ? rel : offers);
}

export async function search(query, zip) {
  const offers = await findOffers(query, zip);
  const cat = await loadCatalog();
  const priced = new Set(offers.map((o) => o.retailer));
  const unpriced = Object.entries(UNPRICED_NOTE).filter(([r]) => !priced.has(r)).map(([retailer, reason]) => ({
    retailer, reason,
    url: retailer === "Giant" ? `https://giantfood.com/product-search/${encodeURIComponent(query)}`
      : retailer === "Aldi" ? `https://www.aldi.us/results?q=${encodeURIComponent(query)}`
      : `https://www.amazon.com/s?k=${encodeURIComponent(query)}&i=amazonfresh`,
  }));
  const top = offers[0];
  const g = top && cat.items.find((i) => i.title === top.title)?.guide;
  const guide = top ? (g
    ? { title: top.title, image: g.photo.src, credit: { author: g.photo.author, license: g.photo.license, page: g.photo.page }, description: g.description, tip: g.tip }
    : { title: top.title, image: top.image, credit: null, description: top.description, tip: null }) : null;
  return { guide, query, zip, demo_mode: true, offers, best: offers[0] ?? null, unpriced, errors: [] };
}

const packQty = (o) => (parseSize(o.size) || parseSize(o.title))?.qty ?? null;

function lineCost(o, unit, refQty, n) {
  const q = packQty(o);
  return unit && o.unit === unit && refQty && q ? o.price * (refQty / q) * n : o.price * n;
}

function amountLabel(unit, refQty) {
  if (!unit || !refQty) return null;
  if (unit === "fl oz" && refQty % 128 === 0) return `${refQty / 128} gal`;
  const amt = +(refQty / DISPLAY_PER[unit]).toFixed(2);
  return unit === "item" ? `${amt} ct` : `${amt} ${unit}`;
}

export async function basket(zip, items) {
  const lines = [];
  for (const it of items) {
    const offers = await findOffers(it.query, zip);
    const best = {};
    offers.forEach((o) => { if (!best[o.retailer]) best[o.retailer] = o; });
    const unit = mainUnit(Object.values(best));
    const sizes = Object.values(best).filter((o) => o.unit === unit).map(packQty).filter(Boolean);
    const counts = {};
    sizes.forEach((s) => (counts[s] = (counts[s] || 0) + 1));
    const refQty = +Object.entries(counts).sort((a, b) => b[1] - a[1] || a[0] - b[0])[0]?.[0] || null;
    lines.push({ q: it.query, n: Math.max(1, it.quantity), best, unit, refQty });
  }
  const retailers = [...new Set(lines.flatMap((l) => Object.keys(l.best)))].sort();
  const stores = retailers.map((r) => {
    let total = 0; const missing = [];
    for (const l of lines) l.best[r] ? (total += lineCost(l.best[r], l.unit, l.refQty, l.n)) : missing.push(l.q);
    return { retailer: r, total: Math.round(total * 100) / 100, complete: !missing.length, missing };
  }).sort((a, b) => (a.complete === b.complete ? a.total - b.total : a.complete ? -1 : 1));

  let splitTotal = 0; const splitItems = []; const notFound = [];
  for (const l of lines) {
    const offers = Object.values(l.best);
    if (!offers.length) { notFound.push(l.q); continue; }
    const cheapest = offers.reduce((a, b) => (lineCost(b, l.unit, l.refQty, l.n) < lineCost(a, l.unit, l.refQty, l.n) ? b : a));
    const cost = lineCost(cheapest, l.unit, l.refQty, l.n);
    splitTotal += cost;
    splitItems.push({ query: l.q, quantity: l.n, cost: Math.round(cost * 100) / 100, amount: amountLabel(l.unit, l.refQty), offer: cheapest });
  }
  const single = stores.find((s) => s.complete);
  return {
    stores,
    split: { total: Math.round(splitTotal * 100) / 100, items: splitItems, retailers: [...new Set(splitItems.map((i) => i.offer.retailer))].sort() },
    best_single_store: single?.retailer ?? null,
    savings_vs_best_single: single ? Math.round((single.total - splitTotal) * 100) / 100 : null,
    not_found: notFound, demo_mode: true,
  };
}

export function instacartLink(items) {
  return `https://www.instacart.com/store/s?k=${encodeURIComponent(items[0]?.query ?? "")}`;
}
