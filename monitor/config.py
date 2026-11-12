"""Impostazioni del radar: cosa cercare, dove, e cosa scartare.

Le keyword "da trovare" stanno in config/keywords.txt (una per riga).
Qui ci sono le liste di parole per riconoscere/scartare/classificare
e le ricerche da lanciare su ogni sito.
"""

# --- Identificativi del club (bastano insieme a una parola "capo") ---------
# Sono confrontati sul titolo normalizzato (minuscolo, senza accenti/punti).
CLUB_PATTERNS = [
    r"\bbari\b",
    r"\bas ?bari\b",
    r"\bssc ?bari\b",
    r"\bfc ?bari\b",
    r"\bbari ?1908\b",
    r"\bgalletti\b",
    r"\basbari ?com\b",
]

# Sponsor di maglia legati solo (o quasi) al Bari: valgono come "Bari"
# se nel titolo c'e' anche una parola capo (maglia/shirt/...).
CLUB_SPONSORS = [
    r"\bwuber\b", r"\bsud ?factoring\b", r"\bsud ?leasing\b",
    r"\bcassa di puglia\b", r"\bgaudianello\b", r"\bradionorba\b",
    r"\bsuissegas\b", r"\bgio ?bi\b", r"\bpasta ambra\b",
    r"\bpuglia promozione\b", r"\bsorgesana\b",
]

# --- Parole "capo" -----------------------------------------------------------
# Maglie da gioco (finiscono nella sezione MAGLIE)
SHIRT_WORDS = [
    r"\bmaglia\b", r"\bmaglie\b", r"\bmaglietta\b", r"\bcasacca\b",
    r"\bdivisa\b", r"\bcompletino\b", r"\bcompleto\b",
    r"\bshirt\b", r"\bjersey\b", r"\bkit\b", r"\btrikot\b", r"\bcamiseta\b",
    r"\bmaillot\b", r"\bcamisola\b", r"\bcamisa\b", r"\bshirts\b",
    r"\bhome\b", r"\baway\b", r"\bthird\b", r"\bfourth\b", r"\bportiere\b",
    r"\bgoalkeeper\b", r"\bgk\b", r"\bmatch worn\b", r"\bmatch issue[d]?\b",
    r"\bplayer issue[d]?\b", r"\bindossata\b", r"\bpreparata\b",
]

# Abbigliamento tecnico (finisce nella sezione ABBIGLIAMENTO).
# Ha la precedenza sulle maglie: "maglia allenamento" va qui.
APPAREL_WORDS = [
    r"\btuta\b", r"\btute\b", r"\btracksuit\b", r"\btrainingsanzug\b",
    r"\bchandal\b", r"\bsurvetement\b", r"\bpantaloncin[oi]\b", r"\bshorts?\b",
    r"\bbermuda\b", r"\bpantaloni\b", r"\bpants\b", r"\bgiubbott[oi]\b",
    r"\bgiubbin[oi]\b", r"\bgiacca\b", r"\bgiacche\b", r"\bgiacchetto\b",
    r"\bjacket\b", r"\bjacke\b", r"\bveste\b", r"\bchaqueta\b",
    r"\bk ?way\b", r"\bwindbreaker\b", r"\bantipioggia\b", r"\bantivento\b",
    r"\bbomber\b", r"\bpiumino\b", r"\bparka\b", r"\bgiaccone\b",
    r"\bfelpa\b", r"\bfelpe\b", r"\bsweat(shirt)?\b", r"\bsweat top\b",
    r"\bhoodie\b", r"\bsudadera\b", r"\bsweater\b",
    r"\ballenamento\b", r"\btraining\b", r"\bentrenamiento\b",
    r"\bpre ?match\b", r"\bprematch\b", r"\bpre gara\b", r"\bwarm ?up\b",
    r"\briscaldamento\b", r"\banthem\b", r"\bcanott[ae]\b", r"\bcanottiera\b",
    r"\bsmanicato\b", r"\bgilet\b", r"\bvest\b", r"\bpolo\b",
    r"\brappresentanza\b", r"\bstaff\b",
]

# --- Esclusioni (vincono su tutto) ------------------------------------------
EXCLUDE_WORDS = [
    # sciarpe, cappelli, accessori
    r"\bsciarp[ae]\b", r"\bscarf\b", r"\bschal\b", r"\bbufanda\b", r"\becharpe\b",
    r"\bcappell[oi]\b", r"\bcappellino\b", r"\bberrett[oi]\b", r"\bbeanie\b",
    r"\bhat\b", r"\bcap\b", r"\bguant[oi]\b", r"\bgloves?\b",
    r"\bcalz[ae]\b", r"\bcalzettoni\b", r"\bsocks?\b", r"\bparastinchi\b",
    r"\bscarp[ae]\b", r"\bscarpini\b", r"\bboots\b", r"\bsneakers?\b",
    r"\bborsa\b", r"\bborsone\b", r"\bzaino\b", r"\bbag\b", r"\bmarsupio\b",
    r"\bportachiavi\b", r"\bkeyring\b", r"\bkeychain\b", r"\bspill[ae]\b",
    r"\bdistintivo\b", r"\bpin\b", r"\bmagnete\b", r"\bcalamita\b",
    r"\bcover\b", r"\bcustodia\b", r"\btazza\b", r"\bmug\b", r"\bborraccia\b",
    r"\bbicchier[ei]\b", r"\bombrello\b", r"\bcuscino\b", r"\bplaid\b",
    r"\blenzuol[ao]\b", r"\baccappatoio\b", r"\basciugamano\b",
    # palloni
    r"\bpallon[ei]\b", r"\bminiball\b", r"\bball\b", r"\bbalon\b", r"\bballon\b",
    # foto, autografi su carta, cimeli
    r"\bfoto\b", r"\bfotografi[ae]\b", r"\bphoto\b", r"\bcartolin[ae]\b",
    r"\bpostcard\b", r"\bautograph card\b", r"\bfigurin[ae]\b", r"\bsticker\b",
    r"\badesiv[oi]\b", r"\balbum\b", r"\bpanini\b", r"\bcimel[ei]\b",
    r"\bgagliardett[oi]\b", r"\bpennant\b", r"\bwimpel\b", r"\bbanderin\b",
    r"\bfanion\b", r"\bbandier[ae]\b", r"\bflag\b", r"\bstendardo\b",
    r"\bmedagli[ae]\b", r"\btrofeo\b", r"\btarga\b", r"\bcoppa\b(?! italia)",
    r"\bbigliett[oi]\b", r"\btickets?\b", r"\babbonamento\b", r"\btessera\b",
    r"\bprogramma\b", r"\bprogramme\b", r"\bposter\b", r"\bmanifesto\b",
    r"\brivista\b", r"\bgiornale\b", r"\bguerin\b", r"\blibr[oi]\b",
    r"\bbook\b", r"\bdvd\b", r"\bvhs\b", r"\bcd\b",
    r"\bminiatura\b", r"\bmini ?kit\b", r"\bstatuett[ae]\b", r"\bfunko\b",
    r"\blego\b", r"\bsubbuteo\b", r"\bpupazzo\b", r"\bpeluche\b",
    r"\bmaglione di natale\b", r"\bscaldacollo\b", r"\bcartella\b", r"\bbarattolo\b",
    r"\blatta\b",
    # altri sport e squadre di Bari che non sono il calcio
    r"\bbasket\b", r"\bpallacanestro\b", r"\bnba\b", r"\bvolley\b",
    r"\bpallavolo\b", r"\brugby\b", r"\bfutsal\b", r"\bcalcio a 5\b",
    r"\bhockey\b", r"\bciclismo\b", r"\bpallanuoto\b",
    r"\bfootball americano\b", r"\bnfl\b",
    # moda: "Bari" e' anche un nome/marchio (Cachet by Bari, A.J. Bari...)
    r"\bby bari\b", r"\ba ?j bari\b", r"\bcachet\b", r"\bfree people\b",
    r"\bdress\b", r"\bpeplum\b", r"\bblouse\b", r"\bskirt\b", r"\bgonna\b",
    r"\bvestito\b", r"\babito\b", r"\bcamicia\b", r"\bcamicetta\b",
    r"\bjeans?\b", r"\bdenim\b", r"\bpaisley\b", r"\bkleid\b", r"\brobe\b",
    # maglie di fantasia, non ufficiali
    r"\bconcept\b", r"\bfan ?made\b", r"\bfantasy\b",
    # gadget/abbigliamento non da calcio
    r"\bcostume\b", r"\bpigiama\b", r"\bbody\b", r"\bbavaglin[oi]\b",
    r"\btutina\b",
]

# Altre squadre dove "Bari" compare solo come zona (es. "Monopoli Bari").
# Scartate se il titolo non dice esplicitamente AS/SSC/FC Bari.
OTHER_CLUBS = [
    r"\bmonopoli\b", r"\blecce\b", r"\bfoggia\b", r"\btaranto\b", r"\bandria\b",
    r"\bbarletta\b", r"\bbisceglie\b", r"\baltamura\b", r"\bmolfetta\b",
    r"\bfasano\b", r"\bbrindisi\b", r"\bcasarano\b", r"\bcerignola\b",
    r"\bmartina\b", r"\bgravina\b", r"\bnoicattaro\b", r"\bcorato\b",
    r"\bbitonto\b", r"\btrani\b", r"\bmanfredonia\b", r"\bnardo\b",
]
CLUB_EXPLICIT = r"\b(as|ssc|fc|us) ?bari\b|\bbari (calcio|1908|fc)\b"

# Le t-shirt "fashion" sono scartate, a meno che siano da allenamento/pre gara.
TSHIRT_PATTERN = r"\bt ?shirts?\b|\btee\b"
TSHIRT_OK = r"allenamento|training|pre ?match|prematch|pre gara|warm ?up|riscaldamento|match"

# --- Classificazione -------------------------------------------------------
TAG_RULES = {
    "match_worn": [r"\bmatch ?worn\b", r"\bmw\b", r"\bindossat[ao]\b",
                    r"\bworn\b", r"\bgetragen\b", r"\bmatchworn\b",
                    r"\busad[ao] en partido\b", r"\bportee\b"],
    "match_issued": [r"\bmatch ?issue[d]?\b", r"\bplayer ?issue[d]?\b",
                      r"\bpreparat[ao]\b", r"\bissued\b",
                      r"\bspec(ifica)? giocatore\b", r"\bplayer spec\b",
                      r"\bmatch prepared\b", r"\bversione giocatore\b"],
    "vintage": [r"\bvintage\b", r"\bretro\b", r"\banni ?[5-9]0\b",
                r"\banni 2000\b", r"\bold school\b", r"\bclassic\b"],
}
VINTAGE_MAX_YEAR = 2014   # stagioni fino a questa = vintage

# Se il titolo non ha l'anno, lo stimiamo da sponsor tecnico o di maglia
# (date dalla lista keyword). Erreà e' escluso: 2005-15 e anche dal 2024.
BRAND_YEAR = {
    r"\bpouchain\b": 1980, r"\bpuma\b": 1979, r"\badidas\b": 1990,
    r"\blotto\b": 2000, r"\bnike\b": 2015, r"\bumbro\b": 2016,
    r"\bzeus\b": 2017, r"\bkappa\b": 2020,
    r"\bcassa di puglia\b": 1985, r"\bsud ?leasing\b": 1988,
    r"\bsud ?factoring\b": 1991, r"\bwuber\b": 1993, r"\bcepu\b": 1996,
    r"\bgio ?bi\b": 1997, r"\btele\b": 1999, r"\bpasta ambra\b": 2004,
    r"\bgaudianello\b": 2007, r"\bradionorba\b": 2010,
    r"\bfashion district\b": 2012, r"\bsuissegas\b": 2014,
    r"\bbetaland\b": 2016, r"\bsorgesana\b": 2019, r"\bbetsson\b": 2025,
}
MODERN_HINTS = [r"\bnuova\b", r"\bnew\b", r"\bbnwt\b", r"\bcon cartellino\b",
                r"\bwith tags\b", r"\bneu\b", r"\bnueva\b"]

# --- Ricerche per sito -------------------------------------------------------
# Poche ricerche ampie: Subito blocca chi fa troppe richieste.
SUBITO_QUERIES = [
    "maglia bari", "as bari", "ssc bari", "tuta bari", "giacca bari",
    "maglia wuber",
]

VINTED = {
    "www.vinted.it": ["maglia bari", "as bari", "ssc bari", "bari vintage",
                      "tuta bari", "giacca bari", "felpa bari",
                      "maglia wuber", "maglia gaudianello"],
    "www.vinted.fr": ["maillot bari"],
    "www.vinted.de": ["bari trikot"],
    "www.vinted.es": ["camiseta bari"],
    "www.vinted.co.uk": ["bari shirt"],
}

WALLAPOP = [
    # (keywords, lat, lon) — Italia e Spagna
    ("maglia bari", 41.1171, 16.8719),
    ("ssc bari", 41.9028, 12.4964),
    ("camiseta bari", 40.4168, -3.7038),
]

# eBay Browse API: (a,b,c) = OR. Una ricerca per riga x ogni marketplace.
EBAY_MARKETPLACES = ["EBAY_IT", "EBAY_DE", "EBAY_GB", "EBAY_US",
                     "EBAY_FR", "EBAY_ES"]
EBAY_QUERIES = [
    "bari (maglia,shirt,jersey,trikot,maillot,camiseta,kit,divisa)",
    "bari (tuta,giacca,felpa,pantaloncini,allenamento,training,jacket,shorts)",
    "(wuber,gaudianello,radionorba,suissegas,sorgesana,cepu) (maglia,shirt,trikot,jersey)",
]

SHOPIFY_STORES = [
    "www.le7sorelle.it",
    "first11shirts.com",
    "www.cultkits.com",
    "classicfootballkit.de",
    "casualfootballshirts.co.uk",
]

WOOCOMMERCE_STORES = [
    # (dominio, filtro sul link per evitare doppioni di lingua)
    ("footballworldgs.it", "/it/"),
]

# Google Programmable Search (opzionale): copre siti che bloccano i robot.
GOOGLE_QUERIES = [
    "maglia bari match worn",
    "bari shirt match issue",
    "maglia ssc bari",
    "maglia as bari vintage",
]
GOOGLE_EVERY_N_RUNS = 8   # ~ ogni 2 ore se il radar gira ogni 15 minuti

MAX_STORED = 5000          # quanti annunci tenere in archivio
MAX_ALERTS_PER_RUN = 25    # oltre, arriva un riepilogo
