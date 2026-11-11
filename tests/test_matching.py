"""Esegui con:  python -m tests.test_matching"""
from monitor.matching import classify

KEEP = {
    "MAGLIA ALLENAMENTO BARI 1992/1993": ("abbigliamento", {"vintage"}),
    "Giacca Bari Adidas 1994/1995": ("abbigliamento", {"vintage"}),
    "maglia home bari adidas ml 1990/1991": ("maglie", {"vintage"}),
    "2002/03 Bari Neqrouz #5 L/S *Match Issue* Home Shirt (XL) Lotto": ("maglie", {"match_issued", "vintage"}),
    "2017-18 Bari Zeus Drittes Trikot XL": ("maglie", set()),
    "Bari Pantaloncino Fourth 202/23 Match Worn Maita – Size L": ("abbigliamento", {"match_worn"}),
    "Bari Away 2004/05 Gazzi – Size XL": ("maglie", {"vintage"}),
    "SSC Bari Maglia gara Away 26-27": ("maglie", {"store"}),
    "Replica Kit Bari 21/22 - M": ("maglie", {"moderna"}),
    "Maglia Adidas Wuber 1993 taglia L": ("maglie", {"vintage"}),
    "SSC BARI 2016 2017 Cassani #6 Match Worn FOOTBALL SHIRT Fußball Trikot Umbro L": ("maglie", {"match_worn"}),
    "Bari 2023/2024 Match Worn And Signed Shirt - Achik 11": ("maglie", {"match_worn"}),
    "Maglia A.S. Bari Lotto Tele+ Cassano 1999": ("maglie", {"vintage"}),
    "Tuta Bari Kappa 2019 rappresentanza": ("abbigliamento", {"moderna"}),
    "1990 91 Bari Le Felpe dei Grandi Sweat Top": ("abbigliamento", {"vintage"}),
    "Camiseta Bari Lotto 2001 retro": ("maglie", {"vintage"}),
    "maglia bari autografata cassano": ("maglie", set()),
}
DROP = [
    "Sciarpa Bari calcio ultras",
    "Pallone autografato SSC Bari",
    "Foto autografata Protti Bari",
    "Gagliardetto AS Bari anni 80",
    "Borsone Bari Adidas 1995/1996",
    "Hamilton Khaki Field 38mm verde acciaio garanzia",
    "2022-23 Genclerbirligi Nike 100 Jahre Jubilaumstrikot Baris #17",
    "2008/09 Czech Republic Baros #15 Home Shirt (L) Puma",
    "Maglia basket Bari NBA",
    "ICONIC - T-shirt SSC Bari San Nicola Stadium bianca",
    "SSC Bari Miniball Ufficiale Errea",
    "Maglione di Natale SSC Bari made in Italy",
    "Cappello pescatore vintage Passion since 1908",
    "Figurina Panini Cassano Bari 1999",
    "England v Italy, World Cup Third Place Jul 1990 - Davies",
    "Maglia Juventus Del Piero 1997",
    "Vintage Cachet by Bari Protas Paisley Puff Sleeve Peplum Jacket",
    "Vintage A.J. Bari New York navy and beige striped shirt dress.",
    "Jean shirt di bari size S",
    "Maglia calcio vintage Jersey Trikot Joma Monopoli Bari lega pro match worn away",
    "2025/26 Bari concept kit",
]


def main():
    bad = 0
    for title, (section, tags) in KEEP.items():
        r = classify(title, "store" if title.startswith("SSC Bari Maglia gara") else "")
        if not r or r["section"] != section or not tags <= set(r["tags"]):
            bad += 1
            print("KEEP FALLITO:", title, "->", r)
    for title in DROP:
        r = classify(title)
        if r:
            bad += 1
            print("DROP FALLITO:", title, "->", r)
    print(f"{len(KEEP) + len(DROP) - bad}/{len(KEEP) + len(DROP)} casi OK")
    raise SystemExit(1 if bad else 0)


if __name__ == "__main__":
    main()
