# udb-foerderkatalog-scraper

Kleiner, robuster Python-Scraper, der alle im **Förderkatalog des Bundes**
erfassten Förderungen für **in Berlin ansässige Förderempfänger** sammelt.
Die Daten dienen der Anreicherung der Berliner Unternehmensdatenbank –
Förderungen sind ein wichtiger Indikator für die Innovationskraft Berlins.

Quelle: [Förderkatalog des Bundes](https://foerderportal.bund.de/foekat/jsp/SucheAction.do?actionMode=searchmask)

## Funktionsweise

Statt hunderte HTML-Ergebnisseiten zu paginieren, nutzt der Scraper den
**CSV-Export** des Förderkatalogs. Das ist deutlich zuverlässiger und liefert
die komplette Trefferliste in einer einzigen Datei. Ablauf:

1. Session aufbauen (Cookies der Suchmaske laden).
2. Detailsuche für **Bundesland = Berlin** abschicken
   (angewendet auf den Förderempfänger/Auftragnehmer, alle Vorhaben inkl.
   abgeschlossener).
3. Gesamte Trefferliste als CSV herunterladen.
4. Trefferzahl gegen die vom Server gemeldete Zahl **validieren**.
5. Rohdaten bereinigen (Encoding `ISO-8859-15` → `UTF-8`, `="..."`-Wrapper
   entfernen, doppelte Geo-Spalten disambiguieren, Fördersumme numerisch
   parsen).
6. Zwei CSV schreiben: eine **je Unternehmen aggregiert** (Summe, Anzahl,
   Zeitraum) und eine **schlanke Detailtabelle je Förderung** (Betrag, Datum,
   Thema) – direkt anschlussfähig für die Unternehmensdatenbank.

Falls der Direktexport unerwartet unvollständig ist, fällt das Skript
automatisch auf eine **Aufteilung nach Laufzeit-Jahren** zurück und
dedupliziert über das Förderkennzeichen (FKZ).

## Nutzung

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Ausgabe

| Datei                              | Inhalt                                                                                                                                                                               |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `foekat_berlin_by_company.csv`   | **Je Unternehmen aggregiert** – eine Zeile je Förderempfänger (Anzahl, Gesamtsumme, Zeitraum). Basis für die Anreicherung der Unternehmensdatenbank.                       |
| `foekat_berlin_foerderungen.csv` | **Je Förderung** – eine schlanke Zeile pro Förderprojekt (Betrag, Zeitraum, Thema). Zeigt, *wie oft*, *wie viel jeweils* und *wann* ein Unternehmen gefördert wurde. |

> Jede Ausgabedatei erhält das Datum der Ausführung als Präfix im Format
> `yyyymmdd_`, z. B. `20260731_foekat_berlin_by_company.csv`.

> Der unveränderte Roh-Export des Servers wird standardmäßig nicht geschrieben.
> Bei Bedarf `roh_speichern = true` in [config.toml](config.toml) setzen → `foekat_berlin_raw.csv`.

### Aggregiert je Unternehmen (`foekat_berlin_by_company.csv`)

Gruppiert über (Förderempfänger, Ort), absteigend nach Gesamtsumme sortiert:

- `Förderempfänger` – Name des Unternehmens/der Organisation
- `Stadt/Gemeinde`, `Ort`, `Bundesland` – Sitz
- `Anzahl_Förderungen` – Anzahl der Förderprojekte
- `Fördersumme_EUR_gesamt` – summierter Bundesanteil über alle Projekte
- `Erste_Laufzeit_von` / `Letzte_Laufzeit_bis` – gesamter Förderzeitraum
- `Ressorts` – beteiligte Bundesressorts (z. B. `BMBF, BMWE`)

#### Beispiel (Stand 2026-07-31: 19.351 Förderungen → 2.983 Unternehmen, Σ ≈ 13,17 Mrd. €)

| Förderempfänger                                         | Ort    | Anzahl_Förderungen | Fördersumme_EUR_gesamt |
| --------------------------------------------------------- | ------ | ------------------: | ----------------------: |
| Technische Universität Berlin                            | Berlin |                2566 |           1250795431.00 |
| Charité - Universitätsmedizin Berlin                    | Berlin |                1091 |           1224831109.00 |
| Gauss Centre for Supercomputing (GCS) e.V.                | Berlin |                   7 |            813440933.00 |
| Senatsverwaltung für Wissenschaft, Gesundheit und Pflege | Berlin |                   2 |            784894686.00 |
| Freie Universität Berlin                                 | Berlin |                1341 |            589833456.00 |

### Je Förderung (`foekat_berlin_foerderungen.csv`)

Eine Zeile pro Förderprojekt, sortiert nach Unternehmen und Datum – so lässt
sich je Unternehmen jede einzelne Förderung mit Betrag und Zeitraum ablesen:

- `Förderempfänger`, `Ort` – gefördertes Unternehmen (Join-Schlüssel zur Aggregat-Datei)
- `FKZ` – Förderkennzeichen (eindeutig je Förderung)
- `Fördersumme_EUR` – Bundesanteil dieser Förderung als Zahl
- `Laufzeit von` / `Laufzeit bis` – Zeitraum dieser Förderung
- `Thema des geförderten Vorhabens` – Beschreibung
- `Ressort`, `Förderart` – Klassifizierung

#### Beispiel (Technische Universität Berlin, älteste Förderungen)

| FKZ      | Fördersumme_EUR | Laufzeit von | Laufzeit bis |
| -------- | ---------------: | ------------ | ------------ |
| WRF2024  |        105033.00 | 06.08.1969   | 31.12.1972   |
| WNW1102  |         10643.00 | 25.08.1970   | 31.12.1973   |
| DV 5207  |        105070.00 | 01.01.1971   | 30.06.1972   |
| DV 5402  |       1397008.00 | 01.07.1971   | 31.12.1973   |
| DV 5402I |        149563.00 | 01.07.1971   | 31.12.1971   |

## Konfiguration

Alle Einstellungen stehen in [config.toml](config.toml) – kein Eingriff in den
Code nötig. Fehlt die Datei oder ein Schlüssel, greifen sinnvolle Standardwerte.

```toml
[suche]
bundesland = "Berlin"   # z. B. "Bayern", "Hamburg"
ziel = "ZE"             # "ZE" = Förderempfänger, "ST" = ausführende Stelle
nur_laufende = false    # true = nur laufende Vorhaben, false = alle

[zeitraum]              # nur für den Jahres-Fallback
jahr_von = 1960
jahr_bis = 2027

[netzwerk]
delay = 1.0             # Sekunden Pause zwischen Requests (fair scrapen)
timeout = 60            # Sekunden pro Request

[ausgabe]
verzeichnis = "data"    # Zielordner (wird bei Bedarf angelegt)
aggregat = "foekat_berlin_by_company.csv"
foerderungen = "foekat_berlin_foerderungen.csv"
roh = "foekat_berlin_raw.csv"
roh_speichern = false   # true → unveränderten Roh-Export zusätzlich schreiben
```

## Projektstruktur

```
main.py            Einstiegspunkt: orchestriert die Pipeline (Client → scrape
                   → write_outputs)
scraper.py         Gesamte Logik: Konfiguration, HTTP-Client, Parsen,
                   Aggregation und Pipeline – in klaren Abschnitten
config.toml        Einstellungen (Bundesland, Zeitraum, Netzwerk, Ausgabe)
requirements.txt   Abhängigkeiten (requests)
data/              Ausgabeordner (datierte CSV, <yyyymmdd>_...)
.github/workflows/ Monatliches Scraping via GitHub Actions
```

## Automatisierung (GitHub Actions)

[.github/workflows/monthly-scrape.yml](.github/workflows/monthly-scrape.yml)
führt den Scraper **am 1. jedes Monats** (04:00 UTC) aus und lässt sich zudem
manuell starten (`workflow_dispatch`). Die beiden aufbereiteten CSV werden nach
`data/` geschrieben und automatisch ins Repository committet – dank Datums-Präfix
entsteht so eine monatliche Historie. Der Roh-Export bleibt via
[.gitignore](.gitignore) ausgeschlossen.

## Hinweise

- Bitte fair scrapen: `DELAY` nicht zu niedrig setzen.
- Encoding der Quelle ist `ISO-8859-15`; die bereinigte Ausgabe ist UTF-8.


## Contributors

Thanks goes to these wonderful people ([emoji key](https://allcontributors.org/docs/en/emoji-key)):

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->

<!-- prettier-ignore-start -->

<!-- markdownlint-disable -->

<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/julizet"><img src="https://avatars.githubusercontent.com/u/52455010?v=4?s=100" width="100px;" alt="Julia Zet"/><br /><sub><b>Julia Zet</b></sub></a><br /><a href="https://github.com/technologiestiftung/udb-foerderkatalog-scraper/commits?author=julizet" title="Code">💻</a> <a href="https://github.com/technologiestiftung/udb-foerderkatalog-scraper/commits?author=julizet" title="Documentation">📖</a></td>
    </tr>
  </tbody>
</table>

<!-- markdownlint-restore -->

<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->

## Credits

<table>
  <tr>
    <td>
      Made by  <a href="https://www.technologiestiftung-berlin.de/">
        <br />
        <br />
        <img width="150" src="https://logos.citylab-berlin.org/logo-technologiestiftung-berlin-de.svg" />
      </a>
    </td>
    <td>
      Supported by <a href="https://www.berlin.de/">
        <br />
        <br />
        <img width="150" src="https://logos.citylab-berlin.org/logo-berlin.svg" />
      </a>
    </td>
  </tr>
</table>
