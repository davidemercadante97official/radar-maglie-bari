"""Valuta se il prezzo di un annuncio e' buono, in linea o caro.

Confronta ogni annuncio con gli annunci simili nell'archivio del radar:
stessa sezione (maglie/abbigliamento), stesso tipo (match worn, match issued,
vintage, moderna, senza etichetta), adulto/bambino e, se ci sono abbastanza
dati, stessa epoca. Il riferimento e' la MEDIANA dei prezzi richiesti, che non
si fa trascinare dai pochi annunci folli.

Limiti: sono prezzi RICHIESTI, non venduti; taglia, condizioni e giocatore
non sono considerati.
"""
from __future__ import annotations

import re
from statistics import median

from .matching import normalize

# Cambi approssimativi verso l'euro (bastano per un confronto di massima).
TO_EUR = {"EUR": 1.0, "GBP": 1.17, "USD": 0.92, "CHF": 1.05}

MIN_COMPS = 5          # sotto questa soglia non diamo un giudizio
GOOD_BELOW = 0.75      # <= 75% della mediana  -> buon prezzo
HIGH_ABOVE = 1.35      # >= 135% della mediana -> caro
KIDS = re.compile(r"\b(bambin[oi]|kids?|junior|youth|ragazz[oi]|baby|neonato|\d{1,2} anni|\d{1,2} ?y(ears)?)\b")
TYPES = ("match_worn", "match_issued", "vintage", "moderna")


def price_eur(item) -> float | None:
    p, cur = item.get("price"), (item.get("currency") or "EUR").upper()
    if p is None or p <= 0 or cur not in TO_EUR:
        return None
    return round(p * TO_EUR[cur], 2)


def _type(item) -> str:
    return next((t for t in TYPES if t in (item.get("tags") or [])), "nd")


def _era(item) -> str:
    y = item.get("year")
    if not y:
        return "?"
    if y < 1990:
        return "<1990"
    if y < 2000:
        return "1990s"
    if y < 2010:
        return "2000s"
    if y < 2018:
        return "2010-17"
    return "2018+"


GARMENTS = [
    ("giacca", re.compile(r"\b(giacc\w*|giubb\w*|jacke?t?|bomber|piumino|parka|k ?way|windbreaker|smanicato|gilet|veste|chaqueta)\b")),
    ("tuta", re.compile(r"\b(tuta|tute|tracksuit|chandal|survetement|trainingsanzug|completo)\b")),
    ("pantaloncini", re.compile(r"\b(pantaloncin\w*|shorts?|bermuda|pantaloni|pants)\b")),
    ("felpa", re.compile(r"\b(felp\w*|sweat\w*|hoodie|sudadera|sweater)\b")),
]


def _garment(item, t) -> str:
    if item.get("section") != "abbigliamento":
        return "maglia"
    return next((name for name, rx in GARMENTS if rx.search(t)), "top")


def _keys(item):
    """Dal confronto piu' preciso al piu' largo."""
    t = normalize(item.get("title", ""))
    kid = bool(KIDS.search(t))
    base = (item.get("section"), _type(item), kid)
    g = _garment(item, t)
    keys = [base + (g, _era(item)), base + (g,)]
    # per le maglie si puo' allargare a tutte le epoche; per l'abbigliamento no:
    # una tuta non si confronta con dei pantaloncini.
    if g == "maglia":
        keys.append(base)
    return keys


def rate_all(listings: list[dict]) -> None:
    """Aggiunge a ogni annuncio: price_eur, price_ref, price_comps, price_rating."""
    pools: dict = {}
    for x in listings:
        x["price_eur"] = price_eur(x)
        # lo store ufficiale ha prezzi di listino: non entra nei confronti
        if x["price_eur"] is None or "store" in (x.get("tags") or []) or x.get("auction"):
            continue
        for k in _keys(x):
            pools.setdefault(k, []).append(x["price_eur"])

    for x in listings:
        for f in ("price_ref", "price_comps", "price_rating"):
            x.pop(f, None)
        if "store" in (x.get("tags") or []):
            x["price_rating"] = "listino"
            continue
        if x["price_eur"] is None or x.get("auction"):
            continue
        others = []
        for k in _keys(x):
            # confronto con gli ALTRI annunci (non con se stesso)
            others = list(pools.get(k, []))
            if x["price_eur"] in others:
                others.remove(x["price_eur"])
            if len(others) >= MIN_COMPS:
                break
        if len(others) < MIN_COMPS:
            continue
        ref = median(others)
        ratio = x["price_eur"] / ref
        x["price_ref"] = round(ref)
        x["price_comps"] = len(others)
        x["price_rating"] = ("buono" if ratio <= GOOD_BELOW
                             else "caro" if ratio >= HIGH_ABOVE else "in_linea")
