"""Marketplace: Subito, Vinted, Wallapop, eBay (API ufficiale)."""
from __future__ import annotations

import base64
import html
import json
import os
import re
import time

from .. import config
from ..net import get, to_float


# --- Subito.it -------------------------------------------------------------
NEXT_DATA = re.compile(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.S)


def subito(ctx):
    out = []
    try:
        for q in config.SUBITO_QUERIES:
            r = get(ctx.http, "https://www.subito.it/annunci-italia/vendita/usato/",
                    params={"q": q, "order": "datedesc"})
            m = NEXT_DATA.search(r.text)
            if not m:
                continue
            data = json.loads(m.group(1))
            items = (data.get("props", {}).get("pageProps", {}).get("initialState", {})
                     .get("items", {}).get("originalList", []))
            for wrap in items:
                it = wrap.get("item", wrap)
                if not it.get("subject"):
                    continue
                urn = it.get("urn", "")
                price = None
                feat = it.get("features") or {}
                pf = feat.get("/price") or {}
                if pf.get("values"):
                    price = to_float(pf["values"][0].get("key"))
                imgs = it.get("images") or []
                img = (imgs[0].get("cdnBaseUrl", "") + "?rule=gallery-desktop-1x-auto") if imgs else ""
                geo = (it.get("geo") or {}).get("town", {}) or {}
                out.append({
                    "native_id": "subito:" + urn.split(":")[-1],
                    "title": it["subject"], "url": (it.get("urls") or {}).get("default", ""),
                    "price": price, "currency": "EUR", "image": img,
                    "source": "subito.it", "location": geo.get("value", ""),
                })
        ctx.ok("subito.it")
    except Exception as e:
        ctx.fail("subito.it", e)
    return out


# --- Vinted (pagina di ricerca) -------------------------------------------------
VINTED_CARD = re.compile(
    r'<img src="(https://images\d*\.vinted\.net/[^"]+)" alt="([^"]+)"[^>]*'
    r'data-testid="product-item-id-(\d+)--image--img"', re.S)


VINTED_MAX_PAGES = 10   # Vinted non mostra oltre 10 pagine (960 annunci)
VINTED_DEEP_PER_RUN = 2


def _vinted_page(ctx, domain, q, page):
    r = get(ctx.http, f"https://{domain}/catalog",
            params={"search_text": q, "order": "newest_first", "page": page})
    out = []
    for img, alt, iid in VINTED_CARD.findall(r.text):
        alt = html.unescape(alt)
        # alt = "Titolo, Brand: X, Condizioni: Y, Taglia: M, 28.00 €, ..."
        title = re.split(r",\s*[A-ZÉÄÖÜ][\wäöüéèà ]{1,20}:\s", alt)[0]
        pm = re.search(r"(\d+[.,]\d{2})\s*(€|£|EUR)", alt)
        slug = re.search(r'href="(/items/%s-[^"?]*)' % iid, r.text)
        out.append({
            "native_id": f"vinted:{iid}", "title": title,
            "url": f"https://{domain}" + (slug.group(1) if slug else f"/items/{iid}"),
            "price": to_float(pm.group(1)) if pm else None,
            "currency": "GBP" if domain.endswith(".co.uk") else "EUR",
            "image": img, "source": domain.replace("www.", ""),
        })
    return out


def vinted(ctx):
    """Ogni giro legge la prima pagina (i piu' recenti) di ogni ricerca.
    In piu' scava nelle pagine 2-10: la prima volta per tutte le ricerche,
    poi a rotazione una ricerca per giro, cosi' in poche ore ripassa tutto
    l'archivio di Vinted senza farsi bloccare. Gli annunci trovati scavando
    sono vecchi: finiscono in dashboard senza notifica."""
    out = []
    searches = [(d, q) for d, qs in config.VINTED.items() for q in qs]
    st = ctx.state.setdefault("vinted", {})
    # leggere tutte le pagine di tutte le ricerche in un giro sola richiede
    # troppo tempo: a ogni giro si scava a fondo in DEEP_PER_RUN ricerche,
    # a rotazione (18+ ricerche -> tutto ripassato in circa 2-3 ore).
    i = st.get("cursor", 0) % len(searches)
    deep = [searches[(i + k) % len(searches)] for k in range(VINTED_DEEP_PER_RUN)]
    st["cursor"] = (i + VINTED_DEEP_PER_RUN) % len(searches)
    for domain in config.VINTED:
        name = domain.replace("www.", "")
        try:
            for d, q in searches:
                if d != domain:
                    continue
                out += _vinted_page(ctx, domain, q, 1)
                if (d, q) not in deep:
                    continue
                for page in range(2, VINTED_MAX_PAGES + 1):
                    got = _vinted_page(ctx, domain, q, page)
                    if not got:
                        break
                    for x in got:
                        x["backfill"] = True
                    out += got
            ctx.ok(name)
        except Exception as e:
            ctx.fail(name, e)
    return out


# --- Wallapop (Spagna/Italia) ---------------------------------------------------
def wallapop(ctx):
    out = []
    # Wallapop restituisce i risultati a pezzi: la prima risposta e' spesso
    # vuota e il resto arriva seguendo "next_page". La prima volta scaviamo a
    # fondo (annunci vecchi, senza notifica), poi seguiamo le prime pagine.
    st = ctx.state.setdefault("wallapop", {})
    first = not st.get("deep_done")
    pages = 25 if first else 10
    try:
        for kw, lat, lon in config.WALLAPOP:
            params = {"keywords": kw, "order_by": "newest", "source": "search_box",
                      "latitude": lat, "longitude": lon}
            items = []
            for _ in range(pages):
                r = get(ctx.http, "https://api.wallapop.com/api/v3/search", params=params,
                        headers={"X-DeviceOS": "0", "Accept": "application/json"})
                j = r.json()
                items += j.get("data", {}).get("section", {}).get("payload", {}).get("items", [])
                nxt = (j.get("meta") or {}).get("next_page")
                if not nxt:
                    break
                params = {"next_page": nxt}
            for it in items:
                imgs = it.get("images") or [{}]
                price = it.get("price") or {}
                host = "it.wallapop.com" if lon > 6 else "es.wallapop.com"
                out.append({
                    "native_id": f"wallapop:{it.get('id')}", "title": it.get("title", ""),
                    "url": f"https://{host}/item/{it.get('web_slug')}",
                    "price": to_float(price.get("amount")), "currency": price.get("currency", "EUR"),
                    "image": (imgs[0].get("urls") or {}).get("medium", ""),
                    "source": "wallapop", "backfill": first,
                })
        ctx.ok("wallapop")
        st["deep_done"] = True
    except Exception as e:
        ctx.fail("wallapop", e)
    return out


# --- eBay Browse API ------------------------------------------------------------
# Servono EBAY_CLIENT_ID e EBAY_CLIENT_SECRET (account developer.ebay.com).
EBAY_DEEP = 1000   # risultati letti per la ricerca "a rotazione" di ogni giro
EBAY_EVERY_MIN = 30


def ebay(ctx):
    cid, secret = os.getenv("EBAY_CLIENT_ID"), os.getenv("EBAY_CLIENT_SECRET")
    if not (cid and secret):
        ctx.skip("ebay", "mancano EBAY_CLIENT_ID / EBAY_CLIENT_SECRET")
        return []
    # le chiavi sono condivise con un'altra app (Radar Cardex): eBay si legge
    # al massimo ogni EBAY_EVERY_MIN minuti, ~1.000 chiamate al giorno su 5.000
    st = ctx.state.setdefault("ebay", {})
    last = st.get("last_call")
    if last and time.time() - last < EBAY_EVERY_MIN * 60 - 120:
        ctx.ok("ebay", f"letto meno di {EBAY_EVERY_MIN} minuti fa")
        return []
    st["last_call"] = time.time()
    out = []
    try:
        tok = ctx.http.post(
            "https://api.ebay.com/identity/v1/oauth2/token",
            headers={"Authorization": "Basic " + base64.b64encode(f"{cid}:{secret}".encode()).decode(),
                     "Content-Type": "application/x-www-form-urlencoded"},
            data={"grant_type": "client_credentials",
                  "scope": "https://api.ebay.com/oauth/api_scope"}, timeout=25)
        tok.raise_for_status()
        token = tok.json()["access_token"]
        # ogni giro: i 200 annunci piu' recenti di ogni ricerca; in piu' una
        # ricerca a rotazione viene letta fino a EBAY_DEEP risultati (annunci
        # vecchi, senza notifica). Circa 22 chiamate a giro.
        searches = [(m, q) for m in config.EBAY_MARKETPLACES for q in config.EBAY_QUERIES]
        first = not st.get("started")
        i = st.get("cursor", 0) % len(searches)
        st["cursor"] = i + 1
        for n, (market, q) in enumerate(searches):
            offsets = range(0, EBAY_DEEP, 200) if n == i else [0]
            for offset in offsets:
                r = ctx.http.get(
                    "https://api.ebay.com/buy/browse/v1/item_summary/search",
                    params={"q": q, "sort": "newlyListed", "limit": 200, "offset": offset},
                    headers={"Authorization": f"Bearer {token}",
                             "X-EBAY-C-MARKETPLACE-ID": market}, timeout=25)
                if r.status_code == 429:
                    raise RuntimeError("limite giornaliero eBay raggiunto")
                r.raise_for_status()
                page = r.json().get("itemSummaries", [])
                if not page:
                    break
                for it in page:
                    price = it.get("price") or it.get("currentBidPrice") or {}
                    legacy = it.get("legacyItemId") or it.get("itemId", "")
                    out.append({
                        "native_id": f"ebay:{legacy}", "title": it.get("title", ""),
                        "url": it.get("itemWebUrl", ""),
                        "price": to_float(price.get("value")), "currency": price.get("currency", ""),
                        "image": (it.get("image") or {}).get("imageUrl", ""),
                        "source": "ebay." + market.split("_")[1].lower().replace("gb", "co.uk").replace("us", "com"),
                        "auction": "AUCTION" in (it.get("buyingOptions") or []),
                        "location": (it.get("itemLocation") or {}).get("country", ""),
                        # primo giro eBay o pagine successive: archivio, niente notifiche
                        "backfill": first or offset > 0,
                    })
                time.sleep(0.3)
        ctx.ok("ebay")
        st["started"] = True
    except Exception as e:
        ctx.fail("ebay", e)
    return out
