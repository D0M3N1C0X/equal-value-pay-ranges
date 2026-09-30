"""
Refreshes the Eurostat snapshots in data/raw/eurostat. Optional: the pipeline reads the snapshots
and never calls the API, so a rebuild does not depend on the API being up or unchanged.

    python src/fetch_eurostat.py

Uses curl, which carries the system's certificates on macOS.
"""
import subprocess
from datetime import date

import config as C

API = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"
GEO = "&".join(f"geo={c}" for c in C.ENTITIES)
QUERIES = {
    C.MARKET_TABLE: f"format=JSON&lang=EN&{GEO}&sex=T&age=TOTAL&sizeclas=GE10",
    C.SIZE_TABLE: f"format=JSON&lang=EN&{GEO}&sex=T&sizeclas=GE1000",
    C.INDEX_TABLE: f"format=JSON&lang=EN&{GEO}&nace_r2=B-S&lcstruct=D11&unit=I20&sinceTimePeriod={C.MARKET_YEAR}",
}


def main() -> None:
    C.EUROSTAT.mkdir(parents=True, exist_ok=True)
    lines = ["file\turl\tretrieved"]
    for name, query in QUERIES.items():
        url = f"{API}/{name}?{query}"
        subprocess.run(["curl", "-sf", "--max-time", "120", "-o", str(C.EUROSTAT / f"{name}.json"), url], check=True)
        lines.append(f"{name}\t{url}\t{date.today().isoformat()}")
        print(f"{name} saved")
    (C.EUROSTAT / "SOURCES.tsv").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
