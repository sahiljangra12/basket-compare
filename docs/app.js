import * as E from "./engine.js?v=6";

const $ = (s, el = document) => el.querySelector(s);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const money = (n) => "$" + Number(n).toFixed(2);
const MD_ZIP = /^2(0[6-9]|1\d)\d{2}$/;
const POPULAR = ["red-seedless-grapes", "bananas", "whole-milk", "large-eggs", "chicken-breast", "strawberries",
  "hass-avocados", "white-bread", "long-grain-white-rice", "ground-beef-80-20", "russet-potatoes", "ground-coffee"];
const CAT_ICON = { Fruit: "grapes", Vegetables: "broccoli", "Dairy & eggs": "glass-of-milk", "Meat & seafood": "cut-of-meat",
  Bakery: "bread", Pantry: "canned-food", Snacks: "popcorn", Drinks: "beverage-box", Frozen: "ice-cream",
  Household: "roll-of-paper", "Personal care": "soap", "Baby & pet": "paw-prints" };
const EXT = '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M6 3h7v7M13 3 4 12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>';

// ---------- state ----------
const store = {
  get(k, d) { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch { return d; } },
  set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch {} },
};
let basket = store.get("bc-basket", []);
let zip = store.get("bc-zip", "21218");
let live = false; // true when a Basket Compare server with real store connections is answering

await E.load();
try {
  const r = await fetch("api/status");
  if (r.ok && (r.headers.get("content-type") || "").includes("json")) live = !(await r.json()).demo_mode;
} catch { /* static hosting: run in the browser */ }
$("#sample-note").hidden = live;
$("#zip").value = zip;

// ---------- prices (browser samples, or the server's live prices) ----------
const cache = new Map();
async function offersFor(item) {
  if (!live) return E.offers(item, zip);
  const key = item.id + zip;
  if (!cache.has(key)) {
    const r = await fetch(`api/search?q=${encodeURIComponent(item.name)}&zip=${zip}`).then((x) => x.json());
    cache.set(key, (r.offers || []).map((o) => ({ ...o, url: o.url || item.links[o.retailer] })));
  }
  return cache.get(key);
}
const cheapest = (item) => (live ? null : E.offers(item, zip)[0]);

function priceHTML(p, perUnit = "") {
  const [d, c] = Number(p).toFixed(2).split(".");
  return `<span class="price" aria-label="${money(p)}${perUnit ? " per " + perUnit : ""}"><sup>$</sup>${d}<span class="cents">${c}</span>${perUnit ? `<span class="per">/${perUnit}</span>` : ""}</span>`;
}
const per = (o) => (o.unit_price != null ? `${money(o.unit_price)}/${o.unit === "item" ? "ea" : o.unit}` : "");

// ---------- small UI helpers ----------
let toastTimer;
function toast(msg) {
  const t = $("#toast");
  t.textContent = msg; t.classList.add("on");
  clearTimeout(toastTimer); toastTimer = setTimeout(() => t.classList.remove("on"), 1800);
}
function show(html, focus = false) {
  const v = $("#view");
  v.innerHTML = html;
  v.classList.remove("enter"); void v.offsetWidth; v.classList.add("enter");
  if (focus) v.focus({ preventScroll: true });
  window.scrollTo(0, 0);
}
function tile(item) {
  const c = cheapest(item);
  return `<li><a class="tile" href="#/p/${item.id}">
    <img src="${item.icon}" alt="" loading="lazy" width="56" height="56">
    <span class="tile-name">${esc(item.name)}</span>
    <span class="tile-size">${esc(item.size)}</span>
    <span class="tile-price">${c ? `from <strong>${money(c.price)}</strong> at ${esc(c.retailer)}` : "Compare prices"}</span>
  </a></li>`;
}

// ---------- categories ----------
$("#cats").innerHTML = E.categories().map((c) =>
  `<a href="#/c/${encodeURIComponent(c)}"><img src="icons/${CAT_ICON[c] || "basket"}.svg" alt="" width="22" height="22">${esc(c)}</a>`).join("");

// ---------- views ----------
function home() {
  show(`<h1 class="view-title">Popular this week</h1>
    <p class="view-sub">Tap an item to compare every store's price, or search for anything above.</p>
    <ul class="tiles">${POPULAR.map(E.byId).filter(Boolean).map(tile).join("")}</ul>`);
}

function category(name) {
  const list = E.items().filter((i) => i.category === name);
  show(`<h1 class="view-title">${esc(name)}</h1><p class="view-sub">${list.length} items</p>
    <ul class="tiles">${list.map(tile).join("")}</ul>`);
}

function results(q) {
  const res = E.search(q, 24);
  $("#q").value = q;
  if (!res.length) {
    const near = E.suggest(q);
    show(`<div class="empty"><h2>No match for “${esc(q)}”</h2>
      <p>${near.length ? "Did you mean one of these?" : "Try a simpler word, like “milk” or “apples”, or browse an aisle above."}</p>
      ${near.length ? `<ul class="tiles">${near.map(tile).join("")}</ul>` : ""}</div>`);
    return;
  }
  const fixed = res[0].fuzzy && !res.some((r) => !r.fuzzy);
  show(`<h1 class="view-title">${res.length} result${res.length > 1 ? "s" : ""} for “${esc(q)}”</h1>
    ${fixed ? `<p class="did-you-mean">Showing matches for <strong>${esc(res[0].item.name.toLowerCase())}</strong> and similar.</p>` : ""}
    <ul class="tiles">${res.map((r) => tile(r.item)).join("")}</ul>`);
}

async function product(id) {
  const item = E.byId(id);
  if (!item) return home();
  const inB = basket.some((b) => b.id === id);
  show(`<a class="back" href="#/" id="back">‹ Back</a>
    <section class="product">
      <div class="product-main">
        <div class="product-icon"><img src="${item.icon}" alt=""></div>
        <div><h1>${esc(item.name)}</h1><p class="product-desc">${esc(item.description)}, ${esc(item.size)}</p></div>
      </div>
      <button class="add${inB ? " added" : ""}" id="add" type="button">${inB ? "In your basket" : "Add to basket"}</button>
    </section>
    <div class="summary" id="summary">Checking prices near ${esc(zip)}…</div>
    <ul class="prices" id="prices"></ul>
    <p class="link-note">Order buttons open that store's page for this item${live ? "" : " (its search results, until the store connection is live)"}.</p>
    <section class="related"><h2>More in ${esc(item.category)}</h2>
      <ul class="tiles">${E.items().filter((i) => i.category === item.category && i.id !== id).slice(0, 6).map(tile).join("")}</ul>
    </section>`, true);
  $("#back").onclick = (e) => { if (cameFromApp) { e.preventDefault(); history.back(); } };
  $("#add").onclick = () => { addToBasket(item); $("#add").textContent = "In your basket"; $("#add").classList.add("added"); };

  const offers = await offersFor(item);
  if (!offers.length) { $("#summary").textContent = "No store near this ZIP has a price for this item right now."; return; }
  const b = offers[0], hi = offers[offers.length - 1];
  const gap = hi.unit_price && b.unit_price ? Math.round((hi.unit_price / b.unit_price - 1) * 100) : 0;
  $("#summary").innerHTML = `<span>Cheapest at <strong>${esc(b.retailer)}</strong>, ${per(b) || money(b.price)}</span>
    ${gap > 0 ? `<span>Up to <strong>${gap}% more</strong> elsewhere</span>` : ""}
    <span>${offers.length} stores near ${esc(zip)}</span>`;
  const byWeight = /^per /.test(item.size); // sold by the pound: the price already is the unit price
  $("#prices").innerHTML = offers.map((o, i) => `
    <li class="row${i === 0 ? " best" : ""}">
      <div class="store">${esc(o.retailer)}${i === 0 ? '<span class="badge">Cheapest</span>' : ""}
        <span class="scope">${o.price_scope === "online" ? "Online price" : "In-store price"}${o.size && o.size !== item.size ? `, ${esc(o.size)}` : ""}</span></div>
      <div class="unit">${byWeight ? "" : o.unit_price != null ? `<strong>${money(o.unit_price)}</strong>per ${esc(o.unit)}` : ""}</div>
      ${priceHTML(o.price, byWeight ? item.size.slice(4) : "")}
      <a class="order" href="${esc(o.url)}" target="_blank" rel="noopener sponsored">Order at ${esc(o.retailer)} ${EXT}</a>
    </li>`).join("");
}

function route() {
  closeSuggest();
  const [, kind, arg] = decodeURIComponent(location.hash).match(/^#\/(\w)\/(.+)$/) || [];
  document.querySelectorAll("#cats a").forEach((a) => a.toggleAttribute("aria-current", kind === "c" && a.textContent === arg));
  if (kind !== "s") $("#q").value = "";
  if (kind === "p") return product(arg);
  if (kind === "c") return category(arg);
  if (kind === "s") return results(arg);
  home();
}
let cameFromApp = false;
window.addEventListener("hashchange", () => { cameFromApp = true; route(); });

// ---------- search box with suggestions ----------
const input = $("#q"), list = $("#suggest");
let active = -1, current = [], t;

function highlight(name, q) {
  const n = E.norm(q);
  const i = name.toLowerCase().indexOf(n);
  return i < 0 || !n ? esc(name) : esc(name.slice(0, i)) + "<mark>" + esc(name.slice(i, i + n.length)) + "</mark>" + esc(name.slice(i + n.length));
}
function closeSuggest() {
  clearTimeout(t); list.hidden = true; active = -1;
  input.setAttribute("aria-expanded", "false"); input.removeAttribute("aria-activedescendant");
  list.querySelectorAll('[aria-selected="true"]').forEach((o) => o.setAttribute("aria-selected", "false"));
}
function renderSuggest() {
  const q = input.value.trim();
  if (!q) return closeSuggest();
  const res = E.search(q, 7);
  current = res.map((r) => r.item);
  let note = "";
  if (!current.length) { current = E.suggest(q); note = current.length ? `No exact match. Did you mean:` : `No match for “${esc(q)}”`; }
  else if (res[0].fuzzy && !res.some((r) => !r.fuzzy)) note = "Did you mean:";
  list.innerHTML = (note ? `<li class="s-note" role="presentation">${note}</li>` : "") + current.map((item, i) => {
    const c = cheapest(item);
    return `<li role="option" id="opt-${i}" data-id="${item.id}" aria-selected="false">
      <img src="${item.icon}" alt="" width="32" height="32">
      <span class="s-name">${highlight(item.name, q)}<span class="s-meta">${esc(item.size)}, ${esc(item.category)}</span></span>
      <span class="s-price">${c ? money(c.price) : ""}</span></li>`;
  }).join("");
  list.hidden = false; input.setAttribute("aria-expanded", "true"); active = -1;
}
function move(d) {
  const opts = [...list.querySelectorAll('[role="option"]')];
  if (!opts.length) return;
  active = (active + d + opts.length) % opts.length;
  opts.forEach((o, i) => o.setAttribute("aria-selected", String(i === active)));
  input.setAttribute("aria-activedescendant", opts[active].id);
  opts[active].scrollIntoView({ block: "nearest" });
}
input.addEventListener("input", () => { clearTimeout(t); t = setTimeout(renderSuggest, 40); });
input.addEventListener("focus", () => input.value && renderSuggest());
input.addEventListener("keydown", (e) => {
  if (e.key === "ArrowDown") { e.preventDefault(); list.hidden ? renderSuggest() : move(1); }
  else if (e.key === "ArrowUp") { e.preventDefault(); move(-1); }
  else if (e.key === "Escape") closeSuggest();
});
list.addEventListener("mousedown", (e) => e.preventDefault()); // keep focus so the click lands
list.addEventListener("click", (e) => {
  const li = e.target.closest('[role="option"]');
  if (li) { input.blur(); location.hash = `#/p/${li.dataset.id}`; }
});
document.addEventListener("click", (e) => { if (!e.target.closest(".search")) closeSuggest(); });
$("#search-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const q = input.value.trim();
  if (!q) return;
  const opt = list.hidden ? null : list.querySelector('[aria-selected="true"]');
  input.blur(); closeSuggest();
  if (opt) { location.hash = `#/p/${opt.dataset.id}`; return; }
  const res = E.search(q, 24);
  // One clear hit: go straight to its prices. Otherwise list the matches.
  location.hash = res.length === 1 || (res.length && E.norm(res[0].item.name) === E.norm(q)) ? `#/p/${res[0].item.id}` : `#/s/${encodeURIComponent(q)}`;
});

// ---------- ZIP ----------
$("#zip").addEventListener("change", (e) => {
  const v = e.target.value.trim();
  if (!MD_ZIP.test(v)) { e.target.value = zip; toast("Enter a Maryland ZIP code, 20600 to 21999"); return; }
  zip = v; store.set("bc-zip", zip); cache.clear(); toast(`Showing prices near ${zip}`); route(); renderBasket();
});

// ---------- basket ----------
const fab = $("#basket-fab"), drawer = $("#drawer"), scrim = $("#scrim");
function addToBasket(item) {
  const line = basket.find((b) => b.id === item.id);
  line ? line.qty++ : basket.push({ id: item.id, qty: 1 });
  store.set("bc-basket", basket); renderBasket();
  fab.classList.remove("bump"); void fab.offsetWidth; fab.classList.add("bump");
  toast(`Added ${item.name.toLowerCase()} to your basket`);
}
function openDrawer(open) {
  drawer.classList.toggle("open", open); drawer.setAttribute("aria-hidden", String(!open));
  fab.setAttribute("aria-expanded", String(open));
  if (open) { scrim.hidden = false; requestAnimationFrame(() => scrim.classList.add("on")); $("#close-drawer").focus(); }
  else { scrim.classList.remove("on"); setTimeout(() => (scrim.hidden = true), 200); }
}
fab.onclick = () => openDrawer(true);
scrim.onclick = () => openDrawer(false);
$("#close-drawer").onclick = () => { openDrawer(false); fab.focus(); };
document.addEventListener("keydown", (e) => { if (e.key === "Escape" && drawer.classList.contains("open")) openDrawer(false); });

async function renderBasket() {
  const count = basket.reduce((n, b) => n + b.qty, 0);
  fab.hidden = !count;
  $("#fab-count").textContent = count;
  const box = $("#basket");
  if (!count) { box.innerHTML = `<p class="b-empty">Your basket is empty. Add items to see which store is cheapest for the whole list.</p>`; openDrawer(false); return; }

  const lines = [];
  for (const b of basket) { const item = E.byId(b.id); if (item) lines.push({ ...b, item, offers: await offersFor(item) }); }
  const r = E.priceBasket(basket, zip, (item) => lines.find((l) => l.id === item.id)?.offers || []);
  $("#fab-total").textContent = money(r.splitTotal);

  box.innerHTML = `
    <ul class="b-lines">${r.lines.map((l) => `
      <li class="b-line">
        <img src="${l.item.icon}" alt="">
        <div><div class="b-name">${esc(l.item.name)}</div>
          <div class="b-where">${l.best ? `${money(l.best.price)} at ${esc(l.best.retailer)}. <a href="${esc(l.best.url)}" target="_blank" rel="noopener sponsored">Order</a>` : "No price yet"}</div></div>
        <div class="qty">
          <button type="button" data-id="${l.id}" data-d="-1" aria-label="One less ${esc(l.item.name)}">−</button>
          <output>${l.qty}</output>
          <button type="button" data-id="${l.id}" data-d="1" aria-label="One more ${esc(l.item.name)}">+</button>
        </div>
      </li>`).join("")}</ul>
    <p class="b-sec">Whole basket at one store</p>
    ${r.stores.map((s) => `<div class="line${s.store === r.bestStore ? " win" : ""}">
      <span>${esc(s.store)}${s.missing.length ? ` <span class="miss">missing ${s.missing.length}</span>` : ""}</span>
      <span class="dots"></span><span class="amt">${money(s.total)}</span></div>`).join("")}
    ${r.splitStores.length > 1 && r.savings > 0
      ? `<p class="tip">Buy each item where it's cheapest (${r.splitStores.map(esc).join(" and ")}) and pay <strong>${money(r.splitTotal)}</strong>, saving ${money(r.savings)}.</p>`
      : r.bestStore ? `<p class="tip"><strong>${esc(r.bestStore)}</strong> is cheapest for everything on your list.</p>` : ""}
    <p class="fine">Totals use each store's price for the usual pack size.</p>
    <button class="clear" id="clear" type="button">Empty basket</button>`;
}
$("#basket").addEventListener("click", (e) => {
  const btn = e.target.closest("button");
  if (!btn) return;
  if (btn.id === "clear") { basket = []; }
  else if (btn.dataset.id) {
    const line = basket.find((b) => b.id === btn.dataset.id);
    line.qty += +btn.dataset.d;
    if (line.qty < 1) basket = basket.filter((b) => b !== line);
  } else return;
  store.set("bc-basket", basket); renderBasket();
});

route();
renderBasket();
