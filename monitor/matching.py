"""Decide se un annuncio e' una maglia/capo del Bari e in che sezione va."""
from __future__ import annotations

import re
import unicodedata
from functools import lru_cache
from pathlib import Path

from . import config

ROOT = Path(__file__).resolve().parent.parent
KEYWORDS_FILE = ROOT / "config" / "keywords.txt"


def normalize(text: str) -> str:
    """minuscolo, senza accenti, punti tolti (A.S. -> as), resto -> spazio."""
    text = (text or "").replace("ß", "ss").replace("ẞ", "ss")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c)).lower()
    text = text.replace("ü", "u")
    text = re.sub(r"(?<=\w)\.(?=\w)", "", text)        # a.s. -> as. ; gio.bi -> giobi
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return f" {text.strip()} "


def _compile(patterns):
    return [re.compile(p) for p in patterns]


CLUB = _compile(config.CLUB_PATTERNS)
SPONSORS = _compile(config.CLUB_SPONSORS)
SHIRT = _compile(config.SHIRT_WORDS)
APPAREL = _compile(config.APPAREL_WORDS)
EXCLUDE = _compile(config.EXCLUDE_WORDS)
OTHER = _compile(config.OTHER_CLUBS)
EXPLICIT = re.compile(config.CLUB_EXPLICIT)
TSHIRT = re.compile(config.TSHIRT_PATTERN)
TSHIRT_OK = re.compile(config.TSHIRT_OK)
TAGS = {k: _compile(v) for k, v in config.TAG_RULES.items()}
MODERN = _compile(config.MODERN_HINTS)
YEAR = re.compile(r"\b(19[5-9]\d|20[0-3]\d)(?: ?(?:\d{2}|\d{4}))?\b")
SHORT_SEASON = re.compile(r"\b([5-9]\d|[0-3]\d) (\d{2})\b")   # "92 93", "21 22"


@lru_cache(maxsize=1)
def keyword_sets() -> list[frozenset[str]]:
    sets = []
    if KEYWORDS_FILE.exists():
        for line in KEYWORDS_FILE.read_text(encoding="utf8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            words = normalize(line).split()
            if words:
                sets.append(frozenset(words))
    return sets


def _any(patterns, text):
    return any(p.search(text) for p in patterns)


def season_year(text: str) -> int | None:
    m = YEAR.search(text)
    if m:
        return int(m.group(1))
    m = SHORT_SEASON.search(text)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        if (a + 1) % 100 == b:          # 92 93 / 99 00 / 21 22
            return 1900 + a if a >= 50 else 2000 + a
    return None


def classify(title: str, source_kind: str = "") -> dict | None:
    """Ritorna {section, tags, year, keyword} oppure None se va scartato.

    section: "maglie" | "abbigliamento"
    tags: sottoinsieme di match_worn, match_issued, vintage, moderna, store
    """
    t = normalize(title)
    words = set(t.split())

    if _any(EXCLUDE, t):
        return None
    if TSHIRT.search(t) and not TSHIRT_OK.search(t):
        return None
    if _any(OTHER, t) and not EXPLICIT.search(t):
        return None

    matched_kw = next((" ".join(sorted(k)) for k in keyword_sets() if k <= words), None)
    has_club = _any(CLUB, t) or _any(SPONSORS, t)
    is_apparel = _any(APPAREL, t)
    is_shirt = _any(SHIRT, t)

    # Lo store ufficiale vende solo Bari: non serve la parola "bari".
    if source_kind == "store":
        has_club = True

    # Nelle case d'asta di maglie (MWS, Memorabid) il titolo spesso e' solo
    # "Giocatore | SSC Bari | partita": basta il nome del club.
    garment_ok = is_shirt or is_apparel or source_kind == "auction"
    if not (matched_kw or (has_club and garment_ok)):
        return None
    # Keyword trovata ma nessun capo nominato (es. "Protti Bari autografo"):
    # se parla di autografi/firme e' quasi sempre un cartoncino, non una maglia.
    if not (is_shirt or is_apparel) and re.search(r"autograf|signed|firmat|signiert", t):
        return None

    section = "abbigliamento" if is_apparel else "maglie"

    tags = [name for name, pats in TAGS.items() if _any(pats, t)]
    year = season_year(t)
    if "vintage" not in tags and year and year <= config.VINTAGE_MAX_YEAR:
        tags.append("vintage")
    if source_kind == "store":
        tags.append("store")
    if not any(x in tags for x in ("vintage", "match_worn", "match_issued", "store")):
        if (year and year > config.VINTAGE_MAX_YEAR) or _any(MODERN, t):
            tags.append("moderna")
    return {"section": section, "tags": tags, "year": year, "keyword": matched_kw}
