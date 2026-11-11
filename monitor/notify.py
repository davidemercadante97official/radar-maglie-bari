"""Notifiche Telegram."""
from __future__ import annotations

import html
import os
import time

import requests

TAG_LABEL = {
    "match_worn": "🔥 MATCH WORN", "match_issued": "🎽 MATCH ISSUED",
    "vintage": "📼 VINTAGE", "moderna": "🆕 MODERNA", "store": "🏪 STORE UFFICIALE",
}
SECTION_LABEL = {"maglie": "Maglia", "abbigliamento": "Abbigliamento"}


def enabled() -> bool:
    return bool(os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID"))


def _api(method: str, **data):
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    data.setdefault("chat_id", os.environ["TELEGRAM_CHAT_ID"])
    r = requests.post(f"https://api.telegram.org/bot{token}/{method}", data=data, timeout=30)
    if r.status_code == 429:  # troppi messaggi: aspettiamo e riproviamo
        time.sleep(int(r.json().get("parameters", {}).get("retry_after", 5)) + 1)
        r = requests.post(f"https://api.telegram.org/bot{token}/{method}", data=data, timeout=30)
    return r


def fmt_price(item) -> str:
    if item.get("price") is None:
        return "asta" if item.get("auction") else "prezzo sul sito"
    sym = {"EUR": "€", "GBP": "£", "USD": "$"}.get(item.get("currency"), item.get("currency", ""))
    p = f"{item['price']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{p} {sym}" + (" (asta)" if item.get("auction") else "")


def caption(item) -> str:
    tags = " · ".join(TAG_LABEL[t] for t in item.get("tags", []) if t in TAG_LABEL)
    lines = [
        f"<b>{html.escape(item['title'])}</b>",
        f"{SECTION_LABEL.get(item['section'], '')}" + (f" · {tags}" if tags else ""),
        f"💶 {fmt_price(item)}",
        f"🛒 {html.escape(item['source'])}" + (f" · {html.escape(item['location'])}" if item.get("location") else ""),
        f'<a href="{html.escape(item["url"], quote=True)}">Apri l\'annuncio</a>',
    ]
    return "\n".join(lines)


def send_item(item) -> bool:
    cap = caption(item)
    if item.get("image"):
        r = _api("sendPhoto", photo=item["image"], caption=cap, parse_mode="HTML")
        if r.ok:
            return True
    r = _api("sendMessage", text=cap, parse_mode="HTML", disable_web_page_preview="false")
    return r.ok


def send_text(text: str) -> bool:
    return _api("sendMessage", text=text, parse_mode="HTML",
                disable_web_page_preview="true").ok
