"""Case d'asta (MatchWornShirt, Memorabid) e ricerca Google opzionale."""
from __future__ import annotations

import html
import os
import re

from .. import config
from ..net import get

LOC = re.compile(r"<loc>([^<]+)</loc>")
OG = re.compile(r'<meta property="og:(title|image)" content="([^"]*)"')


def _og(ctx, url):
    r = get(ctx.http, url)
    meta = dict(OG.findall(r.text))
    return html.unescape(meta.get("title", "")), meta.get("image", "")


# --- MatchWornShirt (mws.com) ---------------------------------------------------
# Gli indirizzi contengono solo il nome del giocatore, quindi confrontiamo la
# sitemap dei lotti attivi con quella del giro prima e apriamo solo i nuovi
# (il titolo della pagina contiene la squadra, es. "Platt | SSC Bari | ...").
def mws(ctx):
    name = "mws.com"
    st = ctx.state.setdefault(name, {})
    out = []
    try:
        xml = get(ctx.http, "https://mws.com/sitemap-products-live.xml").text
        urls = LOC.findall(xml)
        keys = {u.rsplit("-", 1)[-1]: u for u in urls}
        seen = set(st.get("seen", []))
        fresh = [u for k, u in keys.items() if k not in seen]
        if seen:                       # al primo giro memorizziamo e basta
            for u in fresh[:80]:
                title, img = _og(ctx, u)
                if "bari" in title.lower():
                    out.append({"native_id": f"mws:{u.rsplit('-', 1)[-1]}",
                                "title": title.replace(" | MWS", "") + " (MatchWornShirt)",
                                "url": u, "price": None, "currency": "EUR",
                                "image": img, "source": name, "source_kind": "auction",
                                "auction": True})
        st["seen"] = sorted(keys)      # solo i lotti ancora attivi
        ctx.ok(name, f"{len(fresh)} lotti nuovi controllati" if seen else "archivio iniziale creato")
    except Exception as e:
        ctx.fail(name, e)
    return out


# --- Memorabid ----------------------------------------------------------------
def memorabid(ctx):
    name = "memorabid.com"
    st = ctx.state.setdefault(name, {})
    out = []
    try:
        xml = get(ctx.http, "https://www.memorabid.com/it/sitemap-active-auctions.xml").text
        cache = st.setdefault("titles", {})
        for u in LOC.findall(xml):
            if "bari" not in u.lower():
                continue
            aid = u.rstrip("/").rsplit("/", 1)[-1].split("-")[0]
            if aid not in cache:
                cache[aid] = _og(ctx, u)
            title, img = cache[aid]
            out.append({"native_id": f"memorabid:{aid}", "title": title or u.rsplit("/", 1)[-1].replace("-", " "),
                        "url": u, "price": None, "currency": "EUR", "image": img,
                        "source": name, "source_kind": "auction", "auction": True})
        ctx.ok(name)
    except Exception as e:
        ctx.fail(name, e)
    return out


# --- Google Programmable Search (facoltativo) ---------------------------------
# Rete di sicurezza per i siti che bloccano i robot (Catawiki, Depop,
# Classic Football Shirts, Todocoleccion...). 100 ricerche/giorno gratis.
def google(ctx):
    key, cx = os.getenv("GOOGLE_API_KEY"), os.getenv("GOOGLE_CX")
    if not (key and cx):
        ctx.skip("google", "facoltativo: mancano GOOGLE_API_KEY / GOOGLE_CX")
        return []
    st = ctx.state.setdefault("google", {})
    st["run"] = st.get("run", 0) + 1
    if not ctx.seed and st["run"] % config.GOOGLE_EVERY_N_RUNS:
        ctx.ok("google", "in attesa del prossimo giro")
        return []
    out = []
    try:
        for q in config.GOOGLE_QUERIES:
            r = ctx.http.get("https://www.googleapis.com/customsearch/v1",
                             params={"key": key, "cx": cx, "q": q, "num": 10,
                                     "dateRestrict": "d3"}, timeout=25)
            r.raise_for_status()
            for it in r.json().get("items", []):
                pm = it.get("pagemap") or {}
                img = ((pm.get("cse_image") or [{}])[0]).get("src", "")
                host = re.sub(r"^www\.", "", it.get("displayLink", "web"))
                out.append({"native_id": "web:" + it["link"], "title": it.get("title", ""),
                            "url": it["link"], "price": None, "currency": "",
                            "image": img, "source": host})
        ctx.ok("google")
    except Exception as e:
        ctx.fail("google", e)
    return out
