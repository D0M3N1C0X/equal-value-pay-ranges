"""
Writes site/ads.html, the pay range finder, and the Tableau extracts in tableau/.

The finder is one HTML file with its data inlined: no server, no libraries. The extracts are the
tidy tables a Tableau Public workbook reads (see tableau/README.md).
"""
import json

import config as C
import model

TEMPLATE = C.ROOT / "src" / "ads_template.html"


def site_data(o: dict) -> dict:
    r, a, st = o["roles"], o["ads"], o["structure"]
    ranges = {}
    for t in a.itertuples(index=False):
        ranges.setdefault(t.role, {})[t.country] = {
            "annual_min": int(t.annual_min), "annual_max": int(t.annual_max),
            "monthly_min": int(t.monthly_min), "monthly_max": int(t.monthly_max)}
    return {
        "countries": [{"code": c, "name": C.ENTITIES[c], "currency": C.CURRENCY[c], "period": C.AD_PERIOD[c]}
                      for c in C.ENTITIES],
        "families": C.DEPARTMENTS, "levels": C.LEVELS,
        "roles": [{"role": t.role, "family": t.department, "level": t.job_level, "grade": t.grade,
                   "points": int(t.points)} for t in r.itertuples(index=False)],
        "ranges": ranges,
        "grades": {c: [{"grade": g, "min": round(x.min_local), "max": round(x.max_local)}
                       for g, x in st[st["country"] == c].set_index("grade").iterrows()] for c in C.ENTITIES},
    }


def write_site(o: dict) -> None:
    C.SITE.mkdir(exist_ok=True)
    data = json.dumps(site_data(o), ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    html = TEMPLATE.read_text(encoding="utf-8").replace("__DATA__", data)
    (C.SITE / "ads.html").write_text(html, encoding="utf-8")


def write_tableau(o: dict) -> None:
    C.TABLEAU.mkdir(exist_ok=True)
    st = o["structure"].assign(entity=lambda d: d["country"].map(C.ENTITIES),
                               currency=lambda d: d["country"].map(C.CURRENCY))
    st[["country", "entity", "grade", "index", "min", "mid", "max", "currency", "min_local", "mid_local",
        "max_local"]].round(2).to_csv(C.TABLEAU / "structure.csv", index=False)
    p = o["positions"].assign(entity=lambda d: d["country"].map(C.ENTITIES))
    p[["employee_id", "country", "entity", "department", "job_level", "grade", "gender", "fte", "salary", "band_mid",
       "market", "min", "mid", "max", "compa_current", "compa_new", "penetration", "status", "to_min",
       "above_max"]].round(4).to_csv(C.TABLEAU / "positions.csv", index=False)
    mk = o["market"]
    mk[["country", "isco08", "ern", "bns", "base", "aging", "premium", "local", "eur"]].round(4).to_csv(
        C.TABLEAU / "market.csv", index=False)
    o["ads"].drop(columns="text").to_csv(C.TABLEAU / "job_ads.csv", index=False)


def main() -> None:
    o = model.run()
    write_site(o)
    write_tableau(o)
    print("site -> site/ads.html; tableau -> tableau/*.csv")


if __name__ == "__main__":
    main()
