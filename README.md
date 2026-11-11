# 🐓 Radar Maglie Bari

Controlla ogni 15 minuti negozi, marketplace e case d'asta. Appena compare una
maglia (o un capo tecnico) del Bari ti arriva un messaggio su Telegram con foto,
prezzo e link, e l'annuncio finisce nella dashboard web.

Funziona gratis su GitHub: GitHub Actions fa girare il radar, GitHub Pages
ospita la dashboard.

## Cosa controlla

| Tipo | Siti |
|---|---|
| Negozi vintage | le7sorelle.it, footballworldgs.it, first11shirts.com, cultkits.com, classicfootballkit.de, casualfootballshirts.co.uk |
| Store ufficiale | store.sscalciobari.it |
| Marketplace | eBay (IT, DE, UK, US, FR, ES), Subito.it, Vinted (IT, FR, DE, ES, UK), Wallapop |
| Aste | MatchWornShirt (mws.com), Memorabid |
| Facoltativo | Ricerca Google, per i siti che bloccano i robot (Catawiki, Depop, Classic Football Shirts, Todocoleccion) |

**Sezioni della dashboard**
- **Maglie**: maglie da gioco, comprese quelle del portiere.
- **Abbigliamento**: tute, pantaloncini, maglie e canotte da allenamento, pre gara, giubbotti, felpe, polo.

**Etichette**: match worn · match issued · vintage (stagioni fino al 2014) · moderna · store ufficiale.

**Sempre scartati**: sciarpe, palloni, foto, autografi su carta, gagliardetti,
cimeli, figurine, biglietti, cappelli, borse, gadget, t-shirt fashion e maglie di
altri sport.

---

## Messa online, passo per passo (circa 20 minuti)

### 1. Bot Telegram
1. Su Telegram apri **@BotFather** e scrivi `/newbot`. Scegli un nome, per esempio "Radar Bari".
2. BotFather ti dà un **token** (`123456:ABC...`). Conservalo: è il `TELEGRAM_BOT_TOKEN`.
3. Apri il tuo nuovo bot e premi **Avvia** (o scrivigli "ciao").
4. In un browser qualsiasi (PC o telefono) apri questo indirizzo, mettendo il
   tuo token al posto di `TOKEN`, **senza spazi e senza i simboli `< >`**, e
   lasciando la parola `bot` attaccata al token:
   `https://api.telegram.org/botTOKEN/getUpdates`
   Esempio: `https://api.telegram.org/bot123456:ABC-xyz/getUpdates`
   Nella risposta cerca `"chat":{"id":123456789`: quel numero è il `TELEGRAM_CHAT_ID`.
   - Se vedi `"error_code":404`, l'indirizzo è scritto male (di solito manca
     `bot` o sono rimasti `< >` o uno spazio).
   - Se vedi `"result":[]`, scrivi un messaggio al bot e ricarica la pagina.

### 2. eBay (consigliato: è la fonte più grande)
1. Vai su **developer.ebay.com** e registrati (puoi usare il tuo account eBay).
2. Apri *Application Keys* e crea un keyset di **Production**.
3. Copia **App ID (Client ID)** e **Cert ID (Client Secret)**.
4. Se eBay chiede di gestire le notifiche di cancellazione account
   ("Marketplace account deletion"), scegli l'opzione di **esenzione**: il radar
   non salva dati degli utenti eBay.

### 3. GitHub
1. Crea un account su **github.com**.
2. Crea un repository nuovo, per esempio `radar-maglie-bari`, **pubblico**
   (solo così i minuti di Actions sono illimitati e gratuiti).
3. Carica tutti i file di questa cartella: *Add file → Upload files*, oppure con git.
4. Apri *Settings → Secrets and variables → Actions → New repository secret* e
   aggiungi questi secret:

   | Nome | Valore |
   |---|---|
   | `TELEGRAM_BOT_TOKEN` | token di BotFather |
   | `TELEGRAM_CHAT_ID` | il tuo chat id |
   | `EBAY_CLIENT_ID` | App ID di eBay |
   | `EBAY_CLIENT_SECRET` | Cert ID di eBay |
   | `GOOGLE_API_KEY` / `GOOGLE_CX` | facoltativi |

   I secret restano privati anche se il repository è pubblico.
5. Apri *Settings → Pages* e scegli **Deploy from a branch**, branch `main`, cartella `/docs`.
   Dopo un paio di minuti la dashboard è su `https://<tuo-utente>.github.io/radar-maglie-bari/`.
6. Apri *Actions*, scegli **Radar maglie Bari**, poi **Run workflow** per il primo giro.
   Il primo giro crea l'archivio e ti manda un solo messaggio di conferma.
   Dal secondo giro in poi ricevi un messaggio per ogni annuncio nuovo.

> GitHub sospende i workflow pianificati dopo 60 giorni senza attività nel
> repository. Il radar fa un commit a ogni novità, quindi di norma resta attivo.
> Se si ferma, riattivalo dalla scheda *Actions*.

### 4. Ricerca Google: non più disponibile
Google ha chiuso la Custom Search JSON API ai nuovi clienti (gennaio 2026) e la
spegne il 1° gennaio 2027, quindi questo passaggio va saltato. Il radar la
ignora da solo se mancano `GOOGLE_API_KEY` / `GOOGLE_CX`.

Per i siti che bloccano i robot usa i loro avvisi nativi:
- **Subito**: nell'app cerca, tocca *Salva ricerca* e attiva le notifiche
  (es. "maglia bari", "as bari", "ssc bari", "tuta bari", "giacca bari", "maglia wuber").
- **Catawiki**: salva la ricerca "Bari" nella categoria maglie da calcio per
  ricevere le email.

---

## Personalizzare

- **Keyword**: [config/keywords.txt](config/keywords.txt), una per riga. Un
  annuncio corrisponde se il titolo contiene tutte le parole della riga.
- **Esclusioni, sezioni, siti, ricerche**: [monitor/config.py](monitor/config.py).
- **Frequenza**: la riga `cron` in [.github/workflows/monitor.yml](.github/workflows/monitor.yml).

## Provarlo sul PC

```bash
pip install -r requirements.txt truststore
python -m tests.test_matching
python -m monitor.main --dry-run
python -m http.server 8000 -d docs
```
Poi apri http://localhost:8000. `--dry-run` non manda messaggi Telegram.

## Limiti da conoscere

- I siti senza API ufficiale (Vinted, Subito, Wallapop) possono cambiare pagina
  o bloccare i server di GitHub. Il radar continua con gli altri siti e mostra il
  problema in fondo alla dashboard ("Stato dei siti controllati").
- Facebook Marketplace e Instagram non sono coperti: non permettono la lettura automatica.
- MatchWornShirt: il radar segnala i lotti **nuovi** dal primo giro in poi. I
  lotti già online al primo avvio non vengono importati.
