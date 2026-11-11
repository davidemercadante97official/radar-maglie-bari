"""Negozi specializzati: Shopify, WooCommerce e store ufficiale SSC Bari."""
from __future__ import annotations

import html
import re
from urllib.parse import quote_plus

from .. import config
from ..net import get, to_float


import time

SEED_QUERIES = ["bari", "bari home", "bari away", "bari third", "bari maglia",
                "bari shirt", "bari training", "bari match", "bari jacket",
                "bari giacca", "bari tuta", "bari lotto", "bari adidas",
                "bari errea", "bari kappa"]
RUN_QUERIES = ["bari", "bari shirt", "bari maglia", "bari training"]

# --- Shopify ---------------------------------------------------------------
# /products.json elenca i prodotti dal piu' recente: la pagina 1 basta per
# vedere le novita'. Al primo avvio scorriamo piu' pagine per l'archivio.
def shopify(ctx):
    out = []
    for domain in config.SHOPIFY_STORES:
        name = domain.replace("www.", "")
        pages = 6 if ctx.seed else 1
        notes = []
        # 1) catalogo completo dal piu' recente (a volte limitato: non e' grave)
        try:
            for page in range(1, pages + 1):
                r = get(ctx.http, f"https://{domain}/products.json",
                        params={"limit": 250, "page": page})
                products = r.json().get("products", [])
                for p in products:
                    out.append(_shopify_item(domain, name, p))
                if len(products) < 250:
                    break
                time.sleep(2)
        except Exception as e:
            notes.append(f"catalogo non disponibile ({type(e).__name__}), uso la ricerca")
        # 2) ricerca interna del negozio: al primo giro con piu' varianti
        try:
            found = []
            for q in (SEED_QUERIES if ctx.seed else RUN_QUERIES):
                r = get(ctx.http, f"https://{domain}/search/suggest.json",
                        params={"q": q, "resources[type]": "product",
                                "resources[limit]": 10})
                found += r.json()["resources"]["results"].get("products", [])
            for p in found:
                out.append({
                    "native_id": f"{name}:{p.get('handle')}",
                    "title": p.get("title", ""),
                    "url": f"https://{domain}/products/{p.get('handle')}",
                    "price": to_float(p.get("price")),
                    "currency": "GBP" if domain.endswith(".co.uk") else "EUR",
                    "image": (p.get("image") or p.get("featured_image", {}).get("url") or ""),
                    "available": p.get("available", True),
                    "source": name,
                })
            ctx.ok(name, "; ".join(notes))
        except Exception as e:  # un negozio giu' non blocca gli altri
            ctx.fail(name, e)
    return out


def _shopify_item(domain, name, p):
    variants = p.get("variants") or [{}]
    images = p.get("images") or [{}]
    return {
        "native_id": f"{name}:{p.get('handle')}",
        "title": p.get("title", ""),
        "url": f"https://{domain}/products/{p.get('handle')}",
        "price": to_float(variants[0].get("price")),
        "currency": "GBP" if domain.endswith(".co.uk") else "EUR",
        "image": images[0].get("src", ""),
        "available": any(v.get("available", True) for v in variants),
        "source": name,
        "published": p.get("published_at"),
    }


# --- WooCommerce (Store API pubblica) ------------------------------------------
def woocommerce(ctx):
    out = []
    for domain, must_contain in config.WOOCOMMERCE_STORES:
        try:
            for page in range(1, (6 if ctx.seed else 2) + 1):
                r = get(ctx.http, f"https://{domain}/wp-json/wc/store/v1/products",
                        params={"search": "bari", "per_page": 100, "page": page,
                                "orderby": "date", "order": "desc"})
                items = r.json()
                for p in items:
                    link = p.get("permalink", "")
                    if must_contain and must_contain not in link:
                        continue
                    pr = p.get("prices") or {}
                    minor = int(pr.get("currency_minor_unit") or 2)
                    price = to_float(pr.get("price"))
                    out.append({
                        "native_id": f"{domain}:{p.get('id')}",
                        "title": html.unescape(p.get("name", "")),
                        "url": link,
                        "price": price / (10 ** minor) if price is not None else None,
                        "currency": pr.get("currency_code", "EUR"),
                        "image": ((p.get("images") or [{}])[0]).get("src", ""),
                        "available": p.get("is_in_stock", True),
                        "source": domain,
                    })
                if len(items) < 100:
                    break
            ctx.ok(domain)
        except Exception as e:
            ctx.fail(domain, e)
    return out


# --- Store ufficiale SSC Bari ----------------------------------------------------
# Sito su misura: i prodotti hanno indirizzi "Nome_<id>.htm" con id crescenti.
# Leggiamo la home e proviamo gli id successivi all'ultimo visto.
STORE = "https://store.sscalciobari.it/"
STORE_CARD = re.compile(
    r'<a href="([^"]+_(\d+)\.htm)">\s*<img src="([^"]+)"[^>]*alt="([^"]*)"', re.S)
STORE_PRICE = re.compile(r'class="price">\s*([^<]+)<')


def sscbari_store(ctx):
    name = "store.sscalciobari.it"
    st = ctx.state.setdefault(name, {})
    out = {}
    try:
        home = get(ctx.http, STORE).text
        for m in STORE_CARD.finditer(home):
            href, pid, img, alt = m.groups()
            tail = home[m.end(): m.end() + 1500]
            pm = STORE_PRICE.search(tail)
            out[pid] = {
                "native_id": f"sscbari:{pid}", "title": html.unescape(alt),
                "url": STORE + href.lstrip("/"), "image": img,
                "price": to_float(pm.group(1)) if pm else None,
                "currency": "EUR", "source": name, "source_kind": "store",
            }
        ids = [int(x) for x in out] + [st.get("max_id", 0)]
        max_id = max(ids)
        start = 1 if ctx.seed else max_id + 1
        misses = 0
        pid = start
        while misses < (12 if not ctx.seed else 25) and pid < start + 400:
            if str(pid) not in out:
                item = _store_product(ctx, pid)
                if item:
                    out[str(pid)] = item
                    max_id = max(max_id, pid)
                    misses = 0
                elif pid > max_id:
                    misses += 1
            pid += 1
        st["max_id"] = max_id
        ctx.ok(name)
    except Exception as e:
        ctx.fail(name, e)
    return list(out.values())


def _store_product(ctx, pid):
    import time
    for attempt in range(3):
        try:
            r = ctx.http.get(f"{STORE}p_{pid}.htm", timeout=20)
            break
        except Exception:
            time.sleep(3 * (attempt + 1))
    else:
        return None
    time.sleep(0.8)
    if r.status_code != 200:
        return None
    m = re.search(r"<title>\s*(.*?)\s*\|", r.text, re.S)
    title = html.unescape(m.group(1)).strip() if m else ""
    if not title:
        return None
    img = re.search(r'(https://store\.sscalciobari\.it/gestione/img/prodotti/%d/[^"\']+)' % pid, r.text)
    pm = STORE_PRICE.search(r.text)
    return {
        "native_id": f"sscbari:{pid}", "title": title,
        "url": f"{STORE}{quote_plus(title)}_{pid}.htm",
        "image": img.group(1) if img else "",
        "price": to_float(pm.group(1)) if pm else None,
        "currency": "EUR", "source": "store.sscalciobari.it", "source_kind": "store",
    }
