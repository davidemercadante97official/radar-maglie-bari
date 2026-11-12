"""Un giro del radar: legge i siti, filtra, salva, avvisa su Telegram.

Uso:
    python -m monitor.main              # giro normale
    python -m monitor.main --dry-run    # niente Telegram, stampa a video
    python -m monitor.main --only subito,vinted
"""
from __future__ import annotations

import argparse
import json
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

from . import config, notify, pricing
from .matching import classify
from .net import session
from .sources import auctions, marketplaces, shops

ROOT = Path(__file__).resolve().parent.parent
LISTINGS = ROOT / "docs" / "data" / "listings.json"
STATUS = ROOT / "docs" / "data" / "status.json"
STATE = ROOT / "data" / "state.json"

SOURCES = {
    "ebay": marketplaces.ebay,
    "subito": marketplaces.subito,
    "vinted": marketplaces.vinted,
    "wallapop": marketplaces.wallapop,
    "shopify": shops.shopify,
    "woocommerce": shops.woocommerce,
    "store": shops.sscbari_store,
    "mws": auctions.mws,
    "memorabid": auctions.memorabid,
    "google": auctions.google,
}

KIND = {"subito.it": "marketplace", "wallapop": "marketplace"}


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def save(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf8")
    tmp.replace(path)


class Context:
    def __init__(self, state, seed):
        self.http = session()
        self.state = state
        self.seed = seed
        self.status = {}

    def ok(self, name, note=""):
        self.status[name] = {"ok": True, "note": note, "at": now()}

    def fail(self, name, err):
        msg = f"{type(err).__name__}: {err}"[:300]
        self.status[name] = {"ok": False, "note": msg, "at": now()}
        print(f"[ERRORE] {name}: {msg}")

    def skip(self, name, note):
        self.status[name] = {"ok": None, "note": note, "at": now()}


def kind_of(raw) -> str:
    if raw.get("source_kind"):
        return raw["source_kind"]
    src = raw.get("source", "")
    if src.startswith(("ebay", "vinted")) or src in KIND:
        return "marketplace"
    return "shop"


def run(only=None, dry_run=False):
    listings = load(LISTINGS, [])
    state = load(STATE, {})
    seed = not state.get("initialized")
    ctx = Context(state, seed)
    by_id = {x["id"]: x for x in listings}
    started = time.time()
    t = now()

    raw_items = []
    for name, fn in SOURCES.items():
        if only and name not in only:
            continue
        print(f"→ {name}")
        try:
            got = fn(ctx)
            print(f"   {len(got)} risultati grezzi")
            raw_items.extend(got)
        except Exception as e:  # sicurezza: nessuna fonte deve fermare il giro
            traceback.print_exc()
            ctx.fail(name, e)

    new_items, old_found, seen_now = [], [], set()
    for raw in raw_items:
        if not raw.get("title") or not raw.get("url"):
            continue
        kind = kind_of(raw)
        info = classify(raw["title"], kind, strict=raw.get("source", "").startswith("ebay"))
        if not info:
            continue
        iid = raw["native_id"]
        if iid in seen_now:
            continue
        seen_now.add(iid)
        if iid in by_id:
            cur = by_id[iid]
            cur["last_seen"] = t
            if raw.get("price") is not None:
                if cur.get("price") not in (None, raw["price"]):
                    cur["old_price"] = cur["price"]
                cur["price"] = raw["price"]
            cur["available"] = raw.get("available", True)
            cur.update(info)            # se cambiano le regole, si aggiorna
            continue
        item = {
            "id": iid, "title": raw["title"].strip(), "url": raw["url"],
            "price": raw.get("price"), "currency": raw.get("currency", ""),
            "image": raw.get("image", ""), "source": raw.get("source", ""),
            "kind": kind, "auction": bool(raw.get("auction")),
            "location": raw.get("location", ""), "available": raw.get("available", True),
            "first_seen": t, "last_seen": t, **info,
        }
        by_id[iid] = item
        if seed or raw.get("backfill"):
            # archivio iniziale o annuncio vecchio trovato scavando nelle
            # pagine successive: in dashboard, ma senza notifica singola
            item["seed"] = True
            old_found.append(item)
        else:
            new_items.append(item)

    # se le regole sono cambiate, toglie dall'archivio cio' che ora va scartato
    before = len(by_id)
    by_id = {k: x for k, x in by_id.items()
             if classify(x["title"], x.get("kind", ""), strict=x.get("source", "").startswith("ebay"))}
    if len(by_id) < before:
        print(f"Tolti dall'archivio con le regole nuove: {before - len(by_id)}")
    merged = sorted(by_id.values(), key=lambda x: x["first_seen"], reverse=True)[: config.MAX_STORED]
    pricing.rate_all(merged)   # giudizio prezzo: buono / in linea / caro
    print(f"\nNuovi annunci: {len(new_items)}  |  vecchi ritrovati: {len(old_found)}"
          f"  |  in archivio: {len(merged)}")

    sent = 0
    if seed:
        print("Primo avvio: creo l'archivio senza mandare un messaggio per ogni annuncio.")
        if notify.enabled() and not dry_run:
            notify.send_text(f"🐓 <b>Radar maglie Bari attivo</b>\n"
                             f"Archivio iniziale: {len(merged)} annunci.\n"
                             f"Da ora ti scrivo appena ne compare uno nuovo.")
    else:
        for item in new_items[: config.MAX_ALERTS_PER_RUN]:
            print(" +", item["source"], "|", item["title"])
            if notify.enabled() and not dry_run:
                sent += notify.send_item(item)
                time.sleep(1.2)
        extra = len(new_items) - config.MAX_ALERTS_PER_RUN
        if extra > 0 and notify.enabled() and not dry_run:
            notify.send_text(f"…e altri <b>{extra}</b> annunci nuovi: guardali nella dashboard.")
        if len(old_found) >= 5 and notify.enabled() and not dry_run:
            notify.send_text(f"📦 Ho ritrovato <b>{len(old_found)}</b> annunci meno recenti "
                             f"ancora in vendita (pagine successive dei risultati): "
                             f"sono nella dashboard.")

    state["initialized"] = True
    state["last_run"] = t
    save(LISTINGS, merged)
    save(STATE, state)
    prev = load(STATUS, {}).get("sources", {})
    prev.update(ctx.status)
    save(STATUS, {"last_run": t, "seconds": round(time.time() - started, 1),
                  "new": len(new_items), "sent": sent, "total": len(merged),
                  "sources": prev})
    return new_items


def cli():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="non manda messaggi Telegram")
    ap.add_argument("--only", default="", help="fonti separate da virgola: " + ",".join(SOURCES))
    a = ap.parse_args()
    run(only=set(filter(None, a.only.split(","))) or None, dry_run=a.dry_run)


if __name__ == "__main__":
    cli()
