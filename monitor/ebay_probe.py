"""Sonda: per ogni ricerca eBay stampa le categorie degli annunci trovati,
con alcuni titoli d'esempio e se il filtro attuale li terrebbe.
Non salva nulla e non manda messaggi.   python -m monitor.ebay_probe"""
from __future__ import annotations

import base64
import collections
import os

import requests

from . import config
from .matching import classify


def main():
    cid, secret = os.environ["EBAY_CLIENT_ID"], os.environ["EBAY_CLIENT_SECRET"]
    tok = requests.post(
        "https://api.ebay.com/identity/v1/oauth2/token",
        headers={"Authorization": "Basic " + base64.b64encode(f"{cid}:{secret}".encode()).decode(),
                 "Content-Type": "application/x-www-form-urlencoded"},
        data={"grant_type": "client_credentials", "scope": "https://api.ebay.com/oauth/api_scope"},
        timeout=25).json()["access_token"]
    cats = collections.defaultdict(lambda: {"tot": 0, "kept": 0, "ex_kept": [], "ex_drop": []})
    first_raw = None
    for market in config.EBAY_MARKETPLACES:
        for q in config.EBAY_QUERIES:
            r = requests.get("https://api.ebay.com/buy/browse/v1/item_summary/search",
                             params={"q": q, "sort": "newlyListed", "limit": 200},
                             headers={"Authorization": f"Bearer {tok}",
                                      "X-EBAY-C-MARKETPLACE-ID": market}, timeout=25)
            for it in r.json().get("itemSummaries", []):
                if first_raw is None:
                    first_raw = {k: it.get(k) for k in ("categories", "leafCategoryIds")}
                path = " > ".join(c.get("categoryName", c.get("categoryId", "?"))
                                  for c in (it.get("categories") or []))
                key = f"{market} | {(it.get('leafCategoryIds') or ['?'])[0]} | {path}"
                ok = bool(classify(it.get("title", ""), "marketplace", strict=True))
                c = cats[key]
                c["tot"] += 1
                c["kept"] += ok
                lst = c["ex_kept"] if ok else c["ex_drop"]
                if len(lst) < 3:
                    lst.append(it.get("title", "")[:80])
    print("ESEMPIO CAMPI:", first_raw)
    for key, c in sorted(cats.items(), key=lambda kv: -kv[1]["kept"]):
        print(f"\n[{c['kept']}/{c['tot']}] {key}")
        for t in c["ex_kept"]:
            print("   + ", t)
        for t in c["ex_drop"]:
            print("   - ", t)


if __name__ == "__main__":
    main()
