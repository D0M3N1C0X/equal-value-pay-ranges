"""
Reads the Eurostat snapshots in data/raw/eurostat (JSON-stat 2.0) into tidy tables.

The pipeline never calls the API: src/fetch_eurostat.py refreshes the snapshots, and
data/raw/eurostat/SOURCES.tsv records the address and retrieval date of each one.
"""
import itertools
import json

import pandas as pd

import config as C


def read(name: str) -> pd.DataFrame:
    """One row per published cell; unpublished (confidential) cells are simply absent."""
    d = json.loads((C.EUROSTAT / f"{name}.json").read_text(encoding="utf-8"))
    dims = d["id"]
    cats = [sorted(d["dimension"][k]["category"]["index"], key=d["dimension"][k]["category"]["index"].get)
            for k in dims]
    rows = []
    for i, combo in enumerate(itertools.product(*cats)):   # row-major order, last dimension fastest
        v = d["value"].get(str(i))
        if v is not None:
            rows.append({**dict(zip(dims, combo)), "value": float(v)})
    return pd.DataFrame(rows)
