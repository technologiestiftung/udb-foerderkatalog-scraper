#!/usr/bin/env python3
"""Einstiegspunkt für den udb-foerderkatalog-scraper.

Sammelt alle Förderungen für in Berlin ansässige Förderempfänger aus dem
Förderkatalog des Bundes. Einstellungen: config.toml – Logik: scraper.py.

Nutzung:
    pip install -r requirements.txt
    python main.py
"""

import logging
import sys
from datetime import datetime

import requests

from scraper import FoekatClient, log, scrape, write_outputs


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-7s  %(message)s",
        datefmt="%H:%M:%S",
    )
    stamp = datetime.now().strftime("%Y%m%d")   # Datums-Präfix der Ausgabedateien
    try:
        with FoekatClient() as client:      # 1. Session aufbauen (Cookies laden)
            result = scrape(client)         # 2. Suche + CSV-Export (ggf. Jahres-Fallback)
    except requests.RequestException as exc:
        log.error("Netzwerkfehler: %s", exc)
        return 1
    except RuntimeError as exc:
        log.error("%s", exc)
        return 2

    if not result.rows:
        log.warning("Keine Datensätze gefunden – nichts geschrieben.")
        return 3

    write_outputs(result, stamp)            # 3. Aggregat + Detailtabelle schreiben
    return 0


if __name__ == "__main__":
    sys.exit(main())
