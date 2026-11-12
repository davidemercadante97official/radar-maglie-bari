"""Esegui con:  python -m tests.test_pricing"""
from monitor.pricing import profile, similar, rate_all


def item(title, price=100, tags=(), year=None, section="maglie", i=[0]):
    i[0] += 1
    return {"id": str(i[0]), "title": title, "url": f"u{i[0]}", "price": price, "currency": "EUR",
            "tags": list(tags), "year": year, "year_guess": False, "section": section}


SIMILI = [
    ("Maglia Bari Barreto 2010/11 match worn", "Bari 2010-11 Barreto #9 match worn shirt"),
    ("Bari Home 1999/00 Cassano – Size XL", "maglia home Bari Lotto Cassano 1999/2000 taglia L"),
    ("2017/18 Bari Home Shirt (M) Zeus", "Maglia Bari 2017/2018 Zeus"),   # senza versione = home
]
DIVERSE = [
    ("Maglia Bari Barreto 2010/11 match worn", "Maglia Bari Cassano 2010/11 match worn"),   # giocatore
    ("Maglia Bari Barreto 2010/11 match worn", "Maglia Bari Barreto 2011/12 match worn"),   # stagione
    ("Maglia Bari Barreto 2010/11 match worn", "Maglia Bari Barreto 2010/11"),              # tipo
    ("Maglia Bari Barreto 2010/11", "Maglia Bari 2010/11"),                                # con/senza nome
    ("Maglia Bari Cassano 1999/00", "Maglia Bari Cassano 1999/00 autografata"),           # autografo
    ("Maglia Bari 2017/18 home Zeus", "Maglia Bari 2017/18 away Zeus"),                   # versione
    ("Maglia Bari 2017/18 Zeus", "Maglia Bari 2017/18 portiere Zeus"),
    ("Maglia Bari 2023/24 Kappa", "Maglia Bari 2023/24 Kappa edizione speciale LC23"),
    ("Maglia Bari Lotto 1999/00 manica lunga", "Maglia Bari Lotto 1999/00"),
    ("Maglia Bari 1999/00", "Bari Completo 1999/00"),
]


def _p(title):
    from monitor.matching import classify
    c = classify(title) or {}
    return profile({"title": title, "section": c.get("section", "maglie"), "tags": c.get("tags", []),
                    "year": c.get("year"), "year_guess": c.get("year_guess")})


def main():
    bad = 0
    for a, b in SIMILI:
        if not similar(_p(a), _p(b)):
            bad += 1
            print("DOVREBBERO ESSERE SIMILI:", a, "|", b, _p(a), _p(b))
    for a, b in DIVERSE:
        if similar(_p(a), _p(b)):
            bad += 1
            print("NON DOVREBBERO ESSERE SIMILI:", a, "|", b)

    # Barreto non si confronta con Cassano: anche con tanti Cassano costosi
    xs = [item("Maglia Bari Barreto 2010/11", 100, year=2010)]
    xs += [item(f"Maglia Bari Cassano 2010/11 n{i}", 500, year=2010) for i in range(5)]
    xs += [item(f"Maglia Bari Barreto 2010/2011 tg {s}", p, year=2010) for s, p in (("M", 90), ("L", 110), ("XL", 105))]
    rate_all(xs)
    b = xs[0]
    if b["price_rating"] != "in_linea" or b["price_comps"] != 3 or b["price_ref"] != 105:
        bad += 1
        print("BARRETO:", b)
    total = len(SIMILI) + len(DIVERSE) + 1
    print(f"{total - bad}/{total} casi OK")
    raise SystemExit(1 if bad else 0)


if __name__ == "__main__":
    main()
