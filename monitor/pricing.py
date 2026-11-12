"""Valuta se il prezzo di un annuncio e' buono, in linea o caro.

Ogni annuncio si confronta SOLO con annunci SPECIFICAMENTE simili, cioe' che
coincidono su tutti questi punti:
  - sezione e capo (maglia, tuta, giacca, pantaloncini, felpa...)
  - tipo: match worn / match issued (preparata) / normale
  - adulto o bambino
  - stagione (anno esatto; se manca l'anno, solo con altri senza anno)
  - sponsor tecnico (Kappa con Kappa, Adidas con Adidas...)
  - giocatore: il nome stampato o citato nel titolo (Barreto solo con Barreto;
    una maglia senza nome solo con maglie senza nome)
  - autografata o no
  - versione: home / away / terza / portiere / allenamento / edizione speciale
    (se il titolo non la dice vale come home, la maglia standard)
Se i simili specifici sono meno di MIN_COMPS si usa il confronto generico di
prima (stesso tipo ed epoca), ma il giudizio viene segnalato come
"basato su pochi annunci".

Il riferimento e' la MEDIANA dei prezzi richiesti dei simili.
Limiti: sono prezzi RICHIESTI, non venduti; taglia e condizioni non contano.
"""
from __future__ import annotations

import re
from statistics import median

from .matching import normalize

# Cambi approssimativi verso l'euro (bastano per un confronto di massima).
TO_EUR = {"EUR": 1.0, "GBP": 1.17, "USD": 0.92, "CHF": 1.05}

MIN_COMPS = 3          # simili specifici necessari per un giudizio pieno
GENERIC_MIN = 5        # annunci per il giudizio generico ("basato su pochi annunci")
GOOD_BELOW = 0.75      # <= 75% della mediana  -> buon prezzo
HIGH_ABOVE = 1.35      # >= 135% della mediana -> caro
MAX_SHOWN = 5          # quanti simili salviamo per farli vedere

KIDS = re.compile(r"\b(bambin[oi]|kids?|junior|youth|ragazz[oi]|boys?|girls?|baby|neonato|\d{1,2} anni|\d{1,2} ?(y|yrs|years|a))\b")
SIGNED = re.compile(r"\b(autografat\w*|firmat\w*|signed|signiert\w*|autograph\w*|dedicat\w*|firmad\w*|signee)\b")

LONG = re.compile(r"\b(ml|manica lunga|maniche lunghe|long ?sleeves?|l ?s|longsleeve|manches longues|manga larga|langarm)\b")

VARIANTS = [
    ("portiere", re.compile(r"\b(portiere|goalkeeper|gk|keeper|torwart|portero|gardien)\b")),
    ("allenamento", re.compile(r"\b(allenamento|training|pre ?match|prematch|pre gara|warm ?up|riscaldamento|rappresentanza|tempo libero)\b")),
    ("speciale", re.compile(r"\b(special\w*|speciale|limited|limitata|commemorativa|celebrativa|anniversar\w*|centenario|edicion especial|edition speciale|lc23)\b")),
    ("terza", re.compile(r"\b(terza|third|3rd|drittes?|tercera|troisieme|da 3|fourth|quarta)\b")),
    ("away", re.compile(r"\b(away|trasferta|auswarts|auswartstrikot|visitante|exterieur|seconda|2nd)\b")),
    ("home", re.compile(r"\b(home|casa|heim|heimtrikot|local|domicile|prima)\b")),
]

# Parole che NON sono nomi di giocatori: tutto il resto del titolo (parole di
# almeno 3 lettere) viene trattato come nome stampato/citato.
GENERIC = set("""
bari as ssc fc us asbari calcio football soccer club sport sports sportiva societa associazione
galletti galletto biancorossa biancorossi biancorosso biancorosse pugliese puglia italia italy italian
maglia maglie maglietta magliette maglia casacca divisa completino completo kit shirt shirts jersey jerseys
camiseta camisola maillot trikot trikots tricot tee top tank canotta canotte canottiera canotta
football fussball futbol calcio serie lega pro mitropa cup coppa
match worn issued issue player prepared preparata preparato indossata indossato portee porte usada
spec specifica giocatore versione gara partita official ufficiale ufficiali originale originali original
authentic autentica replica fan stadium stadio san nicola
vintage retro classic old school anni years limited edition edizione limitata speciale special
commemorativa celebrativa anniversario anniversary centenario
home away third fourth terza quarta trasferta casa prima seconda portiere goalkeeper keeper training
allenamento rappresentanza riscaldamento warm pre prematch tempo libero relax
manica maniche lunga lunghe corta corte long short sleeve sleeves sleeved longsleeve
taglia tg size sizes small medium large uomo donna man men women unisex adulto adult
bambino bambina bimbo kids kid junior youth anni
nuova nuovo new nuove con senza cartellino etichetta tags tag bnwt bnib ottima ottimo ottime buone buono
condizioni condition conditions perfetta perfette perfetto usata usato used worn washed difetto difetti
leggi descrizione vedi foto read description pilling macchia piccolo piccola
rossa rosso rosse bianca bianco bianche nera nero nere blu azzurra azzurro grigia grigio gialla giallo
red white black blue grey gray yellow rot weiss schwarz rouge blanc noir rojo blanco negro
numero number nummer nome name stampa stampata printed print flock patch patches badge
firmata firmato autografata autografato signed autograph dedica
puma pouchain adidas lotto errea nike umbro zeus kappa macron joma
man cassa sud leasing factoring sudleasing sudfactoring wuber cepu gio giobi tele piu plus
pasta ambra gaudianello radionorba banca popolare fashion district suissegas promozione betaland
the and with for from per con del della dello dei degli delle dal dalla una uno von und der die das
mit les des avec pour por para los las con sin del
felpa felpe giacca giacche giubbotto giubbino giubbotti tuta tute pantaloncino pantaloncini pantaloni
pantalone short shorts pants smanicato gilet bomber piumino parka windbreaker way chaqueta sudadera
sweat sweatshirt hoodie jacket track tracksuit chandal survetement trainingsanzug zip zipper
cotone polyester poliestere termica termico pile polo girocollo
heim auswarts drittes ausweich fussball retro heimtrikot auswartstrikot ml
extra veste survetement survet sweatshirt giubbino sudadera chandal trainingsjacke jacke
xs xl xxl xxxl xxs
cappuccio collezione erre ultras generation passeggio foot gold mens fanbase iconic skyline since passion
silver urban evo awai royal merch stagione saison trenino leggera leggero runner lunghi especial edicion
barattolo legends latta set indossati card mitica mitico magia gillet oro camisa officiel ausschnitt coquette
avant grunge style era garde sammlerstuck custom neuf longues manches vrouwenvoetbalshirt italiaans maat pink
roll neck high deco art rain wonderful non league taupe navy kapp nwt embroidered gift unwanted brand early
boys girls summer bermuda antipioggia scaldacollo cartella checked calciono stagionale ufficio idea regalo
collector collezionisti raro rara rare rarissima introvabile vendo vende cedo bellissima bellissimo
""".split())

TYPES = ("match_worn", "match_issued", "vintage", "moderna")


def price_eur(item) -> float | None:
    p, cur = item.get("price"), (item.get("currency") or "EUR").upper()
    if p is None or p <= 0 or cur not in TO_EUR:
        return None
    return round(p * TO_EUR[cur], 2)


GARMENTS = [
    ("giacca", re.compile(r"\b(giacc\w*|giubb\w*|jacke?t?|bomber|piumino|parka|k ?way|windbreaker|smanicato|gilet|veste|chaqueta)\b")),
    ("pantaloncini", re.compile(r"\b(pantaloncin\w*|shorts?|bermuda)\b")),
    ("pantaloni", re.compile(r"\b(pantalon[ei]|pants|trousers|jogger\w*)\b")),
    ("completo", re.compile(r"\b(complet[oi]n?\w*|full kit|maglia e pantaloncin\w*)\b")),
    ("tuta", re.compile(r"\b(tuta|tute|tracksuit|chandal|survetement|trainingsanzug|completo)\b")),
    ("felpa", re.compile(r"\b(felp\w*|sweat\w*|hoodie|sudadera|sweater)\b")),
    ("polo", re.compile(r"\bpolo\b")),
    ("canotta", re.compile(r"\b(canott\w*|tank|smanicata|vest)\b")),
]

# sponsor tecnico: Kappa con Kappa, Adidas con Adidas...
TECH = re.compile(r"\b(puma|pouchain|adidas|lotto|errea|nike|umbro|zeus|kappa)\b")


def _garment(item, t) -> str:
    default = "top" if item.get("section") == "abbigliamento" else "maglia"
    return next((name for name, rx in GARMENTS if rx.search(t)), default)


def _kind(item) -> str:
    tags = item.get("tags") or []
    if "match_worn" in tags:
        return "match_worn"
    if "match_issued" in tags:
        return "match_issued"
    return "normale"


def _season(item):
    """Anno esatto della stagione. Un anno solo stimato dallo sponsor
    (es. Kappa -> 2020) non e' una stagione precisa: vale come 'non indicata'."""
    y = item.get("year")
    return y if y and not item.get("year_guess") else None


def _names(t: str) -> frozenset:
    words = re.findall(r"[a-z]{3,}", t)
    return frozenset(w for w in words if w not in GENERIC)


def profile(item) -> dict:
    t = normalize(item.get("title", ""))
    return {
        "section": item.get("section"),
        "garment": _garment(item, t),
        "kind": _kind(item),
        "kid": bool(KIDS.search(t)),
        "season": _season(item),
        "brand": (TECH.search(t) or [None])[0],
        "names": _names(t),
        "signed": bool(SIGNED.search(t)),
        "long_sleeve": bool(LONG.search(t)),
        "variant": next((v for v, rx in VARIANTS if rx.search(t)), None),
    }


def similar(a: dict, b: dict) -> bool:
    """True se due profili sono specificamente simili."""
    for k in ("section", "garment", "kind", "kid", "season", "signed", "long_sleeve"):
        if a[k] != b[k]:
            return False
    # sponsor tecnico: se entrambi lo scrivono deve coincidere (se uno non lo
    # scrive, a parita' di stagione e' comunque lo stesso)
    if a["brand"] and b["brand"] and a["brand"] != b["brand"]:
        return False
    if not a["season"] and a["brand"] != b["brand"]:
        return False
    # giocatore: stessi nomi; senza nome solo con senza nome
    # (uno puo' avere qualche parola in piu', es. "Masiello" e "Andrea Masiello")
    na, nb = a["names"], b["names"]
    if na != nb and not (na and nb and (na <= nb or nb <= na)):
        return False
    if (a["variant"] or "home") != (b["variant"] or "home"):
        return False
    return True


def describe(p: dict) -> str:
    """Testo breve di cosa e' stato confrontato (per dashboard e Telegram)."""
    bits = []
    if p["names"]:
        bits.append(" ".join(sorted(n.capitalize() for n in p["names"])))
    else:
        bits.append("senza nome giocatore")
    bits.append(str(p["season"]) if p["season"] else "stagione non indicata")
    if p["brand"]:
        bits.append(p["brand"].capitalize())
    bits.append({"match_worn": "match worn", "match_issued": "match issued"}.get(p["kind"], "non match worn né issued"))
    if p["garment"] != "maglia":
        bits.append(p["garment"])
    if p["variant"]:
        bits.append(p["variant"])
    if p["long_sleeve"]:
        bits.append("maniche lunghe")
    if p["signed"]:
        bits.append("autografata")
    if p["kid"]:
        bits.append("bambino")
    return " · ".join(bits)


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


def _generic_keys(item, p):
    """Confronto GENERICO (il sistema di prima): stessa sezione, tipo,
    adulto/bambino, capo e, se possibile, epoca."""
    typ = next((t for t in TYPES if t in (item.get("tags") or [])), "nd")
    base = (item.get("section"), typ, p["kid"])
    keys = [base + (p["garment"], _era(item)), base + (p["garment"],)]
    if p["garment"] == "maglia":
        keys.append(base)
    return keys


def _verdict(price, ref) -> str:
    ratio = price / ref
    return "buono" if ratio <= GOOD_BELOW else "caro" if ratio >= HIGH_ABOVE else "in_linea"


def rate_all(listings: list[dict]) -> None:
    """Aggiunge a ogni annuncio:
      price_eur, price_rating (buono / in_linea / caro / listino, oppure
      nessun_confronto), price_basis (specifico / pochi), price_ref,
      price_comps, price_match (cosa e' stato confrontato), price_similar.

    1) confronto SPECIFICO (stesso giocatore, stagione, tipo...): con almeno
       MIN_COMPS simili il giudizio e' pieno (basis "specifico");
    2) altrimenti si usa il confronto di prima, piu' generico, e il giudizio
       e' segnalato come "basato su pochi annunci" (basis "pochi")."""
    pool, prof, gpools = [], {}, {}
    for x in listings:
        x["price_eur"] = price_eur(x)
        prof[id(x)] = p = profile(x)
        # store ufficiale (prezzo di listino) e aste (prezzo non finale) esclusi
        if x["price_eur"] is not None and "store" not in (x.get("tags") or []) and not x.get("auction"):
            pool.append(x)
            for k in _generic_keys(x, p):
                gpools.setdefault(k, []).append(x["price_eur"])

    for x in listings:
        p = prof[id(x)]
        for f in ("price_ref", "price_comps", "price_rating", "price_match",
                  "price_similar", "price_basis", "price_specific"):
            x.pop(f, None)
        if "store" in (x.get("tags") or []):
            x["price_rating"] = "listino"
            continue
        if x["price_eur"] is None or x.get("auction"):
            continue

        # 1) simili specifici
        comps = []
        if p["names"] or p["season"]:
            seen = set()
            for y in pool:
                if y is x or y["id"] == x["id"]:
                    continue
                key = (normalize(y["title"]), y["price_eur"])   # niente doppioni
                if key in seen or key == (normalize(x["title"]), x["price_eur"]):
                    continue
                if similar(p, prof[id(y)]):
                    seen.add(key)
                    comps.append(y)
        x["price_specific"] = len(comps)
        if len(comps) >= MIN_COMPS:
            ref = median(c["price_eur"] for c in comps)
            x.update(price_basis="specifico", price_match=describe(p), price_ref=round(ref),
                     price_comps=len(comps), price_rating=_verdict(x["price_eur"], ref),
                     price_similar=[{"title": c["title"], "price_eur": c["price_eur"], "url": c["url"]}
                                    for c in sorted(comps, key=lambda c: c["price_eur"])[:MAX_SHOWN]])
            continue

        # 2) ripiego: confronto generico di prima, segnalato come poco affidabile
        others = []
        for k in _generic_keys(x, p):
            others = list(gpools.get(k, []))
            if x["price_eur"] in others:
                others.remove(x["price_eur"])
            if len(others) >= GENERIC_MIN:
                break
        if len(others) < GENERIC_MIN:
            x["price_rating"] = "nessun_confronto"
            continue
        ref = median(others)
        x.update(price_basis="pochi", price_ref=round(ref), price_comps=len(others),
                 price_rating=_verdict(x["price_eur"], ref),
                 price_match="confronto generico" + (f" (simili specifici: {len(comps)})" if comps else ""))
