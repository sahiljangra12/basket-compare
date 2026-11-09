import * as local from "./engine.js";

const $ = (s) => document.querySelector(s);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const money = (n) => "$" + Number(n).toFixed(2);
const MD_ZIP = /^2(0[6-9]|1\d)\d{2}$/;

// Use the Python server when the page is served by it; otherwise (GitHub Pages) run in the browser.
let server = false;
try {
  const r = await fetch("api/status", { headers: { Accept: "application/json" } });
  if (r.ok && (r.headers.get("content-type") || "").includes("json")) {
    const s = await r.json();
    server = true;
    $("#sample-note").hidden = !s.demo_mode;
  }
} catch { /* static hosting */ }
if (!server) $("#sample-note").hidden = false;

async function post(path, body) {
  const r = await fetch(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.detail || "The price service didn't respond. Try again in a moment.");
  return data;
}

const api = {
  async search(q, zip) {
    if (!server) return local.search(q, zip);
    const r = await fetch(`api/search?q=${encodeURIComponent(q)}&zip=${encodeURIComponent(zip)}`);
    const data = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(data.detail || "The price service didn't respond. Try again in a moment.");
    return data;
  },
  basket: (zip, items) => (server ? post("api/basket", { zip, items }) : local.basket(zip, items)),
  async order(zip, items) {
    if (!server) return { url: local.instacartLink(items) };
    return post("api/order/instacart", { zip, items });
  },
};

// ---- state ----
let basket = [];
try { basket = JSON.parse(localStorage.getItem("basket") || "[]"); } catch { basket = []; }
try { const z = localStorage.getItem("zip"); if (z) $("#zip").value = z; } catch {}
const save = () => { try { localStorage.setItem("basket", JSON.stringify(basket)); } catch {} };
const zip = () => $("#zip").value.trim();
let current = "";

$("#receipt-date").textContent = new Date().toLocaleDateString(undefined, { weekday: "long", month: "long", day: "numeric" });

// ---- shelf tags ----
function priceHTML(p) {
  const [d, c] = Number(p).toFixed(2).split(".");
  return `<span class="price" aria-label="${money(p)}"><span class="cur">$</span>${d}<span class="cents">${c}</span></span>`;
}

function tagHTML(o, i) {
  const best = i === 0 && o.unit_price != null;
  const sale = o.regular_price && o.regular_price > o.price;
  const where = o.price_scope === "online" ? "Online price" : "In-store price";
  const meta = [o.size, o.store].filter(Boolean).map(esc).join(", ");
  // Stock photos are scenes (fill the frame); retailer packshots sit on white (show whole pack).
  const img = o.image
    ? `<div class="tag-photo ${o.image_credit || o.source === "demo" ? "scene" : "pack"}"><img src="${esc(o.image)}" alt="${esc(o.title)}" loading="lazy" onerror="this.parentNode.remove()"></div>`
    : "";
  return `
  <article class="tag${best ? " best" : ""}${sale ? " sale" : ""}">
    <div class="tag-store">${esc(o.retailer)} <small>${best ? `Lowest per ${esc(o.unit)}` : sale ? "On sale" : where}</small></div>
    ${img}
    <div class="tag-body">
      <div class="unit-box">${o.unit_price != null ? `Unit price<strong>${money(o.unit_price)}</strong>per ${esc(o.unit)}` : "Unit price not listed"}</div>
      <div class="price-box">${priceHTML(o.price)}${sale ? `<span class="was">was <s>${money(o.regular_price)}</s></span>` : ""}</div>
    </div>
    <div class="tag-foot">
      <p class="tag-title">${esc(o.title)}</p>
      <p class="tag-meta">${meta}</p>
      <a class="order" href="${esc(o.url)}" target="_blank" rel="noopener sponsored">Order at ${esc(o.retailer)}</a>
    </div>
  </article>`;
}

function productCard(q, data) {
  const g = data.guide || {};
  const offers = data.offers;
  const b = offers[0];
  const stores = new Set(offers.map((o) => o.retailer)).size;
  const sameUnit = offers.filter((o) => o.unit === b.unit && o.unit_price != null).map((o) => o.unit_price);
  const hi = sameUnit.length ? Math.max(...sameUnit) : null;
  const credit = g.credit
    ? `<figcaption>Photo: <a href="${esc(g.credit.page)}" target="_blank" rel="noopener">${esc(g.credit.author)}</a>, ${esc(g.credit.license)}</figcaption>`
    : "";
  const photo = g.image
    ? `<figure class="product-photo"><img src="${esc(g.image)}" alt="${esc(g.title)}" onerror="this.closest('figure').remove()">${credit}</figure>`
    : "";
  return `
  <section class="product${photo ? "" : " no-photo"}">
    ${photo}
    <div class="product-info">
      <h2>${esc(q.charAt(0).toUpperCase() + q.slice(1))}</h2>
      ${g.description ? `<p class="product-desc">${esc(g.description)}</p>` : ""}
      ${g.tip ? `<p class="product-tip"><strong>Buying tip</strong> ${esc(g.tip)}</p>` : ""}
      <div class="product-facts">
        ${b.unit_price != null ? `<div><span>Lowest</span><strong>${money(b.unit_price)}<small>/${esc(b.unit)}</small></strong><em>at ${esc(b.retailer)}</em></div>` : ""}
        ${hi != null && hi > b.unit_price ? `<div><span>Highest</span><strong>${money(hi)}<small>/${esc(b.unit)}</small></strong><em>${Math.round((hi / b.unit_price - 1) * 100)}% more</em></div>` : ""}
        <div><span>Compared</span><strong>${offers.length}</strong><em>prices at ${stores} stores</em></div>
      </div>
      <button class="add-btn" id="add" type="button">Add to basket</button>
    </div>
  </section>`;
}

function inBasket(q) { return basket.some((b) => b.query.toLowerCase() === q.toLowerCase()); }

function renderAddButton() {
  const btn = $("#add");
  if (!btn) return;
  const has = inBasket(current);
  btn.textContent = has ? "Added to basket" : "Add to basket";
  btn.classList.toggle("added", has);
}

async function runSearch(q) {
  q = q.trim();
  const out = $("#results");
  if (q.length < 2) return;
  if (!MD_ZIP.test(zip())) {
    out.innerHTML = `<div class="problem">Enter a 5-digit Maryland ZIP code, between 20600 and 21999, in the box at the top.</div>`;
    $("#zip").focus();
    return;
  }
  current = q;
  document.querySelectorAll("#quick button").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.q === q.toLowerCase())));
  out.innerHTML = `<div class="loading">Checking stores near ${esc(zip())}…</div>`;
  try { localStorage.setItem("zip", zip()); } catch {}
  try {
    const data = await api.search(q, zip());
    if (!data.offers.length) {
      out.innerHTML = `<div class="problem">No prices found for “${esc(q)}”. Try a shorter name, like “grapes” instead of “red grapes 2lb”.</div>`;
    } else {
      out.innerHTML = productCard(q, data) + `<div class="shelf">${data.offers.map(tagHTML).join("")}</div>`;
      $("#add").onclick = () => { if (!inBasket(q)) { basket.push({ query: q, quantity: 1 }); save(); renderBasket(); } renderAddButton(); };
      renderAddButton();
    }
    if (data.unpriced.length) {
      out.insertAdjacentHTML("beforeend", `
        <section class="unpriced">
          <h3>Also worth checking</h3>
          <p>These stores don't share prices yet, so open them directly.</p>
          <ul>${data.unpriced.map((l) => `<li><a href="${esc(l.url)}" target="_blank" rel="noopener">Search ${esc(l.retailer)}</a><span>${esc(l.reason)}</span></li>`).join("")}</ul>
        </section>`);
    }
    if (data.errors?.length) out.insertAdjacentHTML("beforeend", `<div class="problem">${data.errors.map(esc).join(" ")}</div>`);
  } catch (e) {
    out.innerHTML = `<div class="problem">${esc(e.message)}</div>`;
  }
}

// ---- receipt ----
function renderBasket() {
  $("#basket-empty").hidden = basket.length > 0;
  $("#basket-list").innerHTML = basket.map((b, i) => `
    <li><span class="item-name">${esc(b.query)}</span>
      <span class="qty">
        <button type="button" data-i="${i}" data-d="-1" aria-label="One less ${esc(b.query)}">−</button>
        <output>${b.quantity}</output>
        <button type="button" data-i="${i}" data-d="1" aria-label="One more ${esc(b.query)}">+</button>
        <button type="button" class="remove" data-r="${i}" aria-label="Remove ${esc(b.query)}">×</button>
      </span></li>`).join("");
  renderAddButton();
  priceBasket();
}

$("#basket-list").addEventListener("click", (e) => {
  const t = e.target.closest("button");
  if (!t) return;
  if (t.dataset.r != null) basket.splice(+t.dataset.r, 1);
  else { const b = basket[+t.dataset.i]; b.quantity = Math.max(1, b.quantity + +t.dataset.d); }
  save(); renderBasket();
});

async function priceBasket() {
  const box = $("#basket-result");
  if (!basket.length || !MD_ZIP.test(zip())) { box.innerHTML = ""; return; }
  try {
    const r = await api.basket(zip(), basket);
    const lines = r.stores.map((s) => `
      <div class="line${s.retailer === r.best_single_store ? " win" : ""}">
        <span>${esc(s.retailer)}${s.complete ? "" : ` <span class="gap">missing ${s.missing.length}</span>`}</span>
        <span class="dots"></span><span class="amt">${money(s.total)}</span>
      </div>`).join("");
    const split = r.split.retailers.length > 1 && r.savings_vs_best_single > 0
      ? `<p class="split">Shop at ${r.split.retailers.map(esc).join(" and ")} instead and pay ${money(r.split.total)}, saving ${money(r.savings_vs_best_single)}.</p>` : "";
    const amounts = r.split.items.map((i) => esc(i.query) + (i.amount ? ` ${esc(i.amount)}${i.quantity > 1 ? " × " + i.quantity : ""}` : "")).join(", ");
    box.innerHTML = `
      <div class="totals">
        <h3>Whole basket at each store</h3>
        ${lines}${split}
        <p class="fine">Each store is priced for the same amounts (${amounts}) at its best unit price, so pack sizes don't skew the total.</p>
        <button class="order-all" id="order-all" type="button">Order the basket on Instacart</button>
      </div>`;
    $("#order-all").onclick = async () => {
      try { const o = await api.order(zip(), basket); window.open(o.url, "_blank", "noopener"); }
      catch (e) { box.insertAdjacentHTML("beforeend", `<p class="fine">${esc(e.message)}</p>`); }
    };
  } catch (e) {
    box.innerHTML = `<p class="fine">${esc(e.message)}</p>`;
  }
}

// ---- wiring ----
$("#search-form").addEventListener("submit", (e) => { e.preventDefault(); runSearch($("#q").value); });
$("#quick").addEventListener("click", (e) => {
  const q = e.target.closest("button")?.dataset.q;
  if (q) { $("#q").value = q; runSearch(q); }
});
$("#zip").addEventListener("change", () => { if (current) runSearch(current); priceBasket(); });

renderBasket();
