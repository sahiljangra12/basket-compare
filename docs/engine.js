// Basket Compare browser engine: product search (typo-tolerant), sample prices, basket maths.
// Runs entirely in the browser so the site works on GitHub Pages. Prices here are SAMPLES.

let catalog = null;
let index = [];

export async function load() {
  if (catalog) return catalog;
  catalog = await (await fetch("catalog.json?v=6")).json();
  index = catalog.items.map((item, order) => {
    const phrases = [item.name, ...item.aliases].map(norm);
    const words = new Set(phrases.flatMap((p) => p.split(" ")).filter((w) => w.length > 1));
    words.add(norm(item.category));
    const nameWords = new Set(norm(item.name).split(" "));
    return { item, order, phrases, words: [...words], nameWords, name: norm(item.name) };
  });
  return catalog;
}

export const items = () => catalog.items;
export const byId = (id) => catalog.items.find((i) => i.id === id);
export const categories = () => [...new Set(catalog.items.map((i) => i.category))];

// ---------- text matching ----------
export function norm(s) {
  return String(s).toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "")
    .replace(/[^a-z0-9% ]+/g, " ").replace(/\s+/g, " ").trim();
}
const stem = (w) => (w.length > 4 && w.endsWith("es") && !w.endsWith("ses") ? w.slice(0, -2)
  : w.length > 3 && w.endsWith("s") && !w.endsWith("ss") ? w.slice(0, -1) : w);

// Damerau–Levenshtein distance with an early exit once it exceeds `max`.
function distance(a, b, max) {
  if (Math.abs(a.length - b.length) > max) return max + 1;
  const d = Array.from({ length: a.length + 1 }, (_, i) => [i, ...Array(b.length).fill(0)]);
  for (let j = 1; j <= b.length; j++) d[0][j] = j;
  for (let i = 1; i <= a.length; i++) {
    let rowMin = Infinity;
    for (let j = 1; j <= b.length; j++) {
      const cost = a[i - 1] === b[j - 1] ? 0 : 1;
      d[i][j] = Math.min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + cost);
      if (i > 1 && j > 1 && a[i - 1] === b[j - 2] && a[i - 2] === b[j - 1]) d[i][j] = Math.min(d[i][j], d[i - 2][j - 2] + 1);
      rowMin = Math.min(rowMin, d[i][j]);
    }
    if (rowMin > max) return max + 1;
  }
  return d[a.length][b.length];
}
const allowed = (w) => (w.length <= 3 ? 0 : w.length <= 5 ? 1 : 2);

// Score one query word against one product word. Higher is better; 0 means no match.
function wordScore(q, w, isLast) {
  if (q === w || stem(q) === stem(w)) return 10;
  if (w.startsWith(q)) return isLast ? 8 : 6;          // typing in progress: "gra" -> grapes
  if (q.length >= 4 && w.includes(q)) return 4;
  if (q.length === 3 && w.length >= 4 && distance(q, w.slice(0, 4), 1) <= 1 && q[0] === w[0]) return 3; // "mlk" -> milk
  const max = allowed(q);
  if (max) {
    const dist = Math.min(distance(q, w, max), distance(stem(q), stem(w), max),
      isLast && w.length > q.length ? distance(q, w.slice(0, q.length), max) : 99);
    if (dist <= max) return 6 - dist * 2 + (q[0] === w[0] ? 1 : 0); // "graps" -> grapes, "bananna" -> banana
  }
  return 0;
}

/** Search products. Returns [{item, score, fuzzy}] best first. */
export function search(query, limit = 8) {
  const q = norm(query);
  if (!q) return [];
  const qWords = q.split(" ").filter(Boolean);
  const results = [];
  for (const entry of index) {
    let total = 0, fuzzy = false, matched = 0;
    for (let k = 0; k < qWords.length; k++) {
      let best = 0, raw = 0;
      for (const w of entry.words) {
        const sc = wordScore(qWords[k], w, k === qWords.length - 1);
        raw = Math.max(raw, sc);
        best = Math.max(best, sc + (sc && entry.nameWords.has(w) ? 1.5 : 0)); // the product's own name beats aliases
      }
      if (best === 0) continue;
      if (raw < 6) fuzzy = true;
      total += best; matched++;
    }
    if (matched < Math.max(1, qWords.length - (qWords.length > 2 ? 1 : 0))) continue;
    if (matched < qWords.length) fuzzy = true;
    // Prefer products whose own name matches over alias-only matches, and whole-phrase hits.
    if (entry.phrases.some((p) => p === q)) total += 12;
    else if (entry.phrases.some((p) => p.startsWith(q))) total += 6;
    if (entry.name.includes(q)) total += 4;
    total -= entry.name.split(" ").length * 0.3;   // shorter names first: "bananas" before "organic bananas"
    results.push({ item: entry.item, score: total, fuzzy, order: entry.order });
  }
  results.sort((a, b) => b.score - a.score || a.order - b.order);
  // Drop weak guesses when there are clearly better matches ("rice" shouldn't list ribeye).
  const top = results[0]?.score ?? 0;
  return results.filter((r) => r.score >= top * 0.6).slice(0, limit);
}

/** Closest product names when nothing matched, by letter overlap. */
export function suggest(query, limit = 4) {
  const tri = (s) => { const t = new Set(); const p = `  ${norm(s)} `; for (let i = 0; i < p.length - 2; i++) t.add(p.slice(i, i + 3)); return t; };
  const qt = tri(query);
  return index.map((e) => {
    const best = Math.max(...e.phrases.map((p) => { const pt = tri(p); let n = 0; qt.forEach((t) => pt.has(t) && n++); return n / (qt.size + pt.size - n); }));
    return { item: e.item, score: best };
  }).filter((r) => r.score > 0.12).sort((a, b) => b.score - a.score).slice(0, limit).map((r) => r.item);
}

// ---------- sizes and unit prices ----------
const UNITS = {
  lb: ["weight", 16], oz: ["weight", 1], "fl oz": ["volume", 1], gal: ["volume", 128],
  ct: ["count", 1], "sq ft": ["count", 1],
};
const LABEL = { weight: "lb", volume: "fl oz", count: "item" };
const PER = { weight: 16, volume: 1, count: 1 };

export function parseSize(size) {
  const s = String(size).toLowerCase();
  if (s.startsWith("per ")) { const [dim, k] = UNITS[s.slice(4)] || []; return dim ? { qty: k, dim } : null; }
  const m = s.match(/^([\d.]+)\s*(lb|oz|fl oz|gal|ct|sq ft)\b/);
  if (!m) return null;
  const [dim, k] = UNITS[m[2]];
  return { qty: parseFloat(m[1]) * k, dim };
}

export function unitPrice(price, size) {
  const s = parseSize(size);
  if (!s) return { unit_price: null, unit: null };
  const label = s.dim === "count" && /sq ft/.test(size) ? "sq ft" : LABEL[s.dim];
  return { unit_price: price / (s.qty / PER[s.dim]), unit: label };
}

// ---------- sample prices ----------
function noise(...parts) {
  let h = 2166136261;
  for (const ch of parts.join("|")) { h ^= ch.charCodeAt(0); h = Math.imul(h, 16777619); }
  return 0.9 + ((h >>> 0) % 2000) / 10000;
}
const STORE_SCOPE = { Walmart: "online", "Amazon Fresh": "online" };

/** Every store's offer for one product, cheapest per unit first. */
export function offers(item, zip) {
  return item.stores.map((store) => {
    let price = item.price * catalog.index[store] * noise(item.id, store, zip);
    price = Math.max(0.25, Math.round(price * 100) / 100 - (price > 2 ? 0.01 : 0));
    price = Math.round(price * 100) / 100;
    return {
      retailer: store, title: item.name, size: item.size, price,
      ...unitPrice(price, item.size),
      url: item.links[store], price_scope: STORE_SCOPE[store] || "store", source: "demo",
    };
  }).sort((a, b) => (a.unit_price ?? a.price) - (b.unit_price ?? b.price));
}

/** Price a basket [{id, qty}] at every store, plus the cheapest mix of stores. */
export function priceBasket(lines, zip, offersFor = (item) => offers(item, zip)) {
  const priced = lines.map((l) => ({ ...l, item: byId(l.id) })).filter((l) => l.item)
    .map((l) => ({ ...l, offers: offersFor(l.item) }));
  const stores = catalog.stores.map((store) => {
    let total = 0; const missing = [];
    for (const l of priced) {
      const o = l.offers.find((x) => x.retailer === store);
      o ? (total += o.price * l.qty) : missing.push(l.item.name);
    }
    return { store, total: Math.round(total * 100) / 100, missing };
  }).filter((s) => s.missing.length < priced.length)
    .sort((a, b) => a.missing.length - b.missing.length || a.total - b.total);
  const split = priced.map((l) => ({ ...l, best: l.offers[0] }));
  const splitTotal = Math.round(split.reduce((t, l) => t + l.best.price * l.qty, 0) * 100) / 100;
  const single = stores.find((s) => !s.missing.length);
  return {
    lines: split, stores, splitTotal,
    bestStore: single?.store ?? null,
    savings: single ? Math.round((single.total - splitTotal) * 100) / 100 : 0,
    splitStores: [...new Set(split.map((l) => l.best.retailer))],
  };
}
