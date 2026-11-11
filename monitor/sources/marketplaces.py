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


def vinted(ctx):
    out = []
    for domain, queries in config.VINTED.items():
        try:
            for q in queries:
                r = get(ctx.http, f"https://{domain}/catalog",
                        params={"search_text": q, "order": "newest_first"})
                for img, alt, iid in VINTED_CARD.findall(r.text):
                    alt = html.unescape(alt)
                    # alt = "Titolo, Brand: X, Condizioni: Y, Taglia: M, 28.00 €, ..."
                    # taglia via ", Brand: / Marke: / Zustand: / Taille: ..."
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
            ctx.ok(domain.replace("www.", ""))
        except Exception as e:
            ctx.fail(domain.replace("www.", ""), e)
    return out


# --- Wallapop (Spagna/Italia) ---------------------------------------------------
def wallapop(ctx):
    out = []
    try:
        for kw, lat, lon in config.WALLAPOP:
            r = get(ctx.http, "https://api.wallapop.com/api/v3/search",
                    params={"keywords": kw, "order_by": "newest", "source": "search_box",
                            "latitude": lat, "longitude": lon},
                    headers={"X-DeviceOS": "0", "Accept": "application/json"})
            items = r.json().get("data", {}).get("section", {}).get("payload", {}).get("items", [])
            for it in items:
                imgs = it.get("images") or [{}]
                price = it.get("price") or {}
                host = "it.wallapop.com" if lon > 6 else "es.wallapop.com"
                out.append({
                    "native_id": f"wallapop:{it.get('id')}", "title": it.get("title", ""),
                    "url": f"https://{host}/item/{it.get('web_slug')}",
                    "price": to_float(price.get("amount")), "currency": price.get("currency", "EUR"),
                    "image": (imgs[0].get("urls") or {}).get("medium", ""),
                    "source": "wallapop",
                })
        ctx.ok("wallapop")
    except Exception as e:
        ctx.fail("wallapop", e)
    return out


# --- eBay Browse API ------------------------------------------------------------
# Servono EBAY_CLIENT_ID e EBAY_CLIENT_SECRET (account developer.ebay.com).
def ebay(ctx):
    cid, secret = os.getenv("EBAY_CLIENT_ID"), os.getenv("EBAY_CLIENT_SECRET")
    if not (cid and secret):
        ctx.skip("ebay", "mancano EBAY_CLIENT_ID / EBAY_CLIENT_SECRET")
        return []
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
        for market in config.EBAY_MARKETPLACES:
            for q in config.EBAY_QUERIES:
                r = ctx.http.get(
                    "https://api.ebay.com/buy/browse/v1/item_summary/search",
                    params={"q": q, "sort": "newlyListed", "limit": 200},
                    headers={"Authorization": f"Bearer {token}",
                             "X-EBAY-C-MARKETPLACE-ID": market}, timeout=25)
                if r.status_code == 429:
                    raise RuntimeError("limite giornaliero eBay raggiunto")
                r.raise_for_status()
                for it in r.json().get("itemSummaries", []):
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
                    })
                time.sleep(0.3)
        ctx.ok("ebay")
    except Exception as e:
        ctx.fail("ebay", e)
    return out
