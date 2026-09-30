"""
The pay-range model in pandas. Every function has a twin in the Excel workbook built by
build_workbook.py, written with the same order of operations so the two agree.

    roles()       36 roles: job evaluation points, grade, ISCO occupation
    market()      Eurostat earnings by occupation and country, aged to mid-2026, large-employer premium
    grade_index() the current progression between grades, with the family premiums averaged out
    structure()   one range per grade per country: market level x grade index, then the spread
    positions()   every employee against the new range: compa-ratio, status, cost to minimum
    ads()         the range to publish in a job advertisement (Article 5), per role and country
"""
import hashlib
import math

import numpy as np
import pandas as pd

import config as C
import eurostat


def verify_sources() -> None:
    for path, digest in ((C.SOURCE_EMPLOYEES, C.SOURCE_SHA256), (C.SOURCE_EVALUATION, C.EVALUATION_SHA256)):
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise SystemExit(f"{path} does not match the pinned checksum")


def grade_for(points: float) -> str:
    return [g for floor, g in C.GRADES if points >= floor][-1]


def roles() -> pd.DataFrame:
    r = pd.read_csv(C.SOURCE_EVALUATION)
    r["points"] = sum(r[f] * w for f, w in C.FACTOR_WEIGHTS.items())
    r["grade"] = r["points"].map(grade_for)
    isco = pd.read_csv(C.ISCO_MAP)
    r = r.merge(isco[["department", "job_level", "isco08"]], on=["department", "job_level"], validate="one_to_one")
    r["department"] = pd.Categorical(r["department"], C.DEPARTMENTS, ordered=True)
    r = r.sort_values(["department", "job_level"]).reset_index(drop=True)
    r["department"] = r["department"].astype(str)
    return r[["role", "department", "job_level", *C.FACTORS, "points", "grade", "isco08"]]


# ---- Market -------------------------------------------------------------------------------------

def index_table() -> pd.DataFrame:
    """Labour cost index (wages and salaries), and the factor that ages 2022 earnings to mid-2026."""
    t = eurostat.read(C.INDEX_TABLE).pivot(index="geo", columns="time", values="value")
    t.columns = [int(c) for c in t.columns]
    out = pd.DataFrame({
        "lci_base": t[C.MARKET_YEAR], "lci_prev": t[C.INDEX_LATEST - 1], "lci_latest": t[C.INDEX_LATEST]},
        index=pd.Index(list(C.ENTITIES), name="country"))
    out["growth"] = out["lci_latest"] / out["lci_prev"] - 1
    out["aging"] = out["lci_latest"] / out["lci_base"] * (out["lci_latest"] / out["lci_prev"]) ** C.UPDATE_YEARS
    return out


def earnings(table: str) -> pd.DataFrame:
    e = eurostat.read(table)
    e = e[e["unit"] == "NAC"].pivot_table(index=["geo", "isco08"], columns="indic_se", values="value")
    return e.reset_index()


def premium_table() -> pd.DataFrame:
    """Earnings in enterprises of 1,000+ against 10+, where Eurostat publishes both."""
    small = earnings(C.MARKET_TABLE).set_index(["geo", "isco08"])["ERN"]
    large = earnings(C.SIZE_TABLE).set_index(["geo", "isco08"])["ERN"]
    rows = [{"country": c, "isco08": o, "ern_10": small[(c, o)], "ern_1000": large[(c, o)]}
            for c in C.PREMIUM_COUNTRIES for o in C.PREMIUM_OCCUPATIONS]
    t = pd.DataFrame(rows)
    t["ratio"] = t["ern_1000"] / t["ern_10"]
    return t


def premium() -> float:
    return float(premium_table()["ratio"].median())


def market(r: pd.DataFrame | None = None) -> pd.DataFrame:
    """Market base pay for each occupation the roles use, full time, per year, in euro and local currency."""
    r = roles() if r is None else r
    occupations = sorted(r["isco08"].unique())
    e = earnings(C.MARKET_TABLE)
    e = e[e["geo"].isin(list(C.ENTITIES)) & e["isco08"].isin(occupations)]
    idx = index_table()
    p = premium()
    rows = []
    for c in C.ENTITIES:
        for o in occupations:
            cell = e[(e["geo"] == c) & (e["isco08"] == o)].iloc[0]
            base = cell["ERN"] - cell["BNS"]
            local = base * idx.loc[c, "aging"] * p
            fx = C.EUR_PLN if C.CURRENCY[c] == "PLN" else 1.0
            rows.append({"country": c, "isco08": o, "ern": cell["ERN"], "bns": cell["BNS"], "base": base,
                         "aging": idx.loc[c, "aging"], "premium": p, "local": local, "fx": fx, "eur": local / fx})
    return pd.DataFrame(rows)


# ---- Employees and the current structure -------------------------------------------------------

def employees(r: pd.DataFrame | None = None, mk: pd.DataFrame | None = None) -> pd.DataFrame:
    verify_sources()
    r = roles() if r is None else r
    mk = market(r) if mk is None else mk
    e = pd.read_csv(C.SOURCE_EMPLOYEES, parse_dates=["hire_date", "exit_date"])
    when = pd.Timestamp(C.SNAPSHOT)
    e = e[(e["hire_date"] <= when) & (e["exit_date"].isna() | (e["exit_date"] > when))]
    e = e[e["country"].isin(list(C.ENTITIES))].sort_values("employee_id").reset_index(drop=True)
    e = e.merge(r[["department", "job_level", "points", "grade", "isco08"]], on=["department", "job_level"],
                how="left", validate="many_to_one")
    e = e.merge(mk[["country", "isco08", "eur"]].rename(columns={"eur": "market"}), on=["country", "isco08"],
                how="left", validate="many_to_one")
    return e[["employee_id", "country", "department", "job_level", "gender", "fte", "base_salary_eur",
              "salary_band_mid_eur", "points", "grade", "isco08", "market"]].rename(
        columns={"base_salary_eur": "salary", "salary_band_mid_eur": "band_mid"})


def current_bands(e: pd.DataFrame) -> pd.DataFrame:
    """The company's band midpoint for each role and country (one value per cell in the HRIS)."""
    b = e.groupby(["country", "department", "job_level", "grade"], observed=True)["band_mid"].agg(["min", "max"])
    assert (b["min"] == b["max"]).all(), "a role has more than one band midpoint in a country"
    return b["min"].rename("band_mid").reset_index()


def grade_index(bands: pd.DataFrame) -> pd.Series:
    """How much each grade's midpoint is above the reference grade's in the current bands, family by
    family averaged out: geometric mean of the role midpoints in the grade, relative to the reference
    grade, per country, then the geometric mean across countries; finally each grade at least
    MIN_PROGRESSION above the one below."""
    b = bands.assign(ln=np.log(bands["band_mid"]))
    g = b.groupby(["country", "grade"])["ln"].mean().unstack()          # ln of the geometric mean
    rel = g.sub(g[C.REFERENCE_GRADE], axis=0)                           # ln ratio to grade D
    grades = [g_ for _, g_ in C.GRADES]
    raw = np.exp(rel[grades].mean())
    smooth = []
    for g_ in grades:
        smooth.append(raw[g_] if not smooth else max(raw[g_], smooth[-1] * (1 + C.MIN_PROGRESSION)))
    return pd.Series(smooth, index=grades, name="index")


def raw_grade_index(bands: pd.DataFrame) -> pd.Series:
    b = bands.assign(ln=np.log(bands["band_mid"]))
    g = b.groupby(["country", "grade"])["ln"].mean().unstack()
    rel = g.sub(g[C.REFERENCE_GRADE], axis=0)
    return np.exp(rel[[g_ for _, g_ in C.GRADES]].mean()).rename("raw")


# ---- New structure ------------------------------------------------------------------------------

def structure(e: pd.DataFrame, index: pd.Series) -> pd.DataFrame:
    """Midpoint = country level x grade index. The country level makes the new midpoints of the
    current non-managerial workforce add up to the large-employer market for the same occupations,
    times the positioning policy."""
    rows = []
    for c in C.ENTITIES:
        g = e[(e["country"] == c) & e["grade"].isin(C.LEVEL_GRADES)]
        level = C.POSITIONING[c] * g["market"].sum() / g["grade"].map(index).sum()
        fx = C.EUR_PLN if C.CURRENCY[c] == "PLN" else 1.0
        for _, grade in C.GRADES:
            s = C.SPREAD[grade]
            mid = level * index[grade]
            lo = mid * 2 / (2 + s)
            rows.append({"country": c, "grade": grade, "level": level, "index": index[grade], "spread": s,
                         "min": lo, "mid": mid, "max": lo * (1 + s),
                         "min_local": lo * fx, "mid_local": mid * fx, "max_local": lo * (1 + s) * fx})
    return pd.DataFrame(rows)


def positions(e: pd.DataFrame, st: pd.DataFrame, idx: pd.DataFrame) -> pd.DataFrame:
    p = e.merge(st[["country", "grade", "min", "mid", "max"]], on=["country", "grade"], validate="many_to_one")
    p = p.sort_values("employee_id").reset_index(drop=True)
    p["compa_current"] = p["salary"] / p["band_mid"]
    p["compa_new"] = p["salary"] / p["mid"]
    p["penetration"] = (p["salary"] - p["min"]) / (p["max"] - p["min"])
    p["status"] = np.where(p["salary"] < p["min"], "Below", np.where(p["salary"] > p["max"], "Above", "Within"))
    p["to_min"] = (p["min"] - p["salary"]).clip(lower=0) * p["fte"]
    p["above_max"] = (p["salary"] - p["max"]).clip(lower=0) * p["fte"]
    growth = p["country"].map(idx["growth"])
    p["years_to_absorb"] = np.where(p["status"] == "Above",
                                    np.log(p["salary"] / p["max"]) / np.log(1 + growth), 0.0)
    return p


def summary(p: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for c in C.ENTITIES:
        g = p[p["country"] == c]
        rows.append({
            "country": c, "headcount": len(g),
            # payroll against market on the non-managerial grades, the basis of the country level
            "payroll": g.loc[g["grade"].isin(C.LEVEL_GRADES), "salary"].sum(),
            "market": g.loc[g["grade"].isin(C.LEVEL_GRADES), "market"].sum(),
            "compa_new": g["compa_new"].mean(), "compa_current": g["compa_current"].mean(),
            "below": (g["status"] == "Below").sum(), "within": (g["status"] == "Within").sum(),
            "above": (g["status"] == "Above").sum(),
            "to_min": g["to_min"].sum(), "above_max": g["above_max"].sum(),
            "below_women": ((g["status"] == "Below") & (g["gender"] == "F")).sum(),
            "women": (g["gender"] == "F").sum(),
            "below_men": ((g["status"] == "Below") & (g["gender"] == "M")).sum(),
            "men": (g["gender"] == "M").sum(),
            "to_min_women": g.loc[g["gender"] == "F", "to_min"].sum(),
        })
    s = pd.DataFrame(rows)
    s["ratio"] = s["payroll"] / s["market"]
    return s


def by_family(p: pd.DataFrame) -> pd.DataFrame:
    f = p.groupby(["country", "department"])["compa_new"].mean().unstack("country")
    return f.reindex(index=C.DEPARTMENTS, columns=list(C.ENTITIES))


def family_premium(bands: pd.DataFrame) -> pd.DataFrame:
    """Within each grade and country, the highest current band midpoint over the lowest."""
    g = bands.groupby(["country", "grade"])["band_mid"].agg(["min", "max"])
    g["ratio"] = g["max"] / g["min"]
    return g.reset_index()


# ---- Job advertisements -------------------------------------------------------------------------

def round_out(lo: float, hi: float, step: float) -> tuple[float, float]:
    return math.floor(lo / step) * step, math.ceil(hi / step) * step


def ads(r: pd.DataFrame, st: pd.DataFrame) -> pd.DataFrame:
    rows = []
    s = st.set_index(["country", "grade"])
    for role in r.itertuples(index=False):
        for c in C.ENTITIES:
            x = s.loc[(c, role.grade)]
            cur = C.CURRENCY[c]
            a_lo, a_hi = round_out(x["min_local"], x["max_local"], C.AD_STEP[cur])
            m_lo, m_hi = round_out(x["min_local"] / 12, x["max_local"] / 12, C.AD_MONTHLY_STEP)
            monthly = C.AD_PERIOD[c] == "month"
            lo, hi = (m_lo, m_hi) if monthly else (a_lo, a_hi)
            rows.append({"role": role.role, "department": role.department, "job_level": role.job_level,
                         "grade": role.grade, "country": c, "currency": cur, "period": C.AD_PERIOD[c],
                         "annual_min": a_lo, "annual_max": a_hi, "monthly_min": m_lo, "monthly_max": m_hi,
                         "text": f"{cur} {lo:,.0f} – {hi:,.0f} gross per {C.AD_PERIOD[c]}, full time"})
    return pd.DataFrame(rows)


def sample(per_cell: int, seed: int = 7) -> pd.DataFrame:
    """A few employees from every country, department and level, so every formula has data."""
    e = employees()
    parts = [g.sample(n=min(len(g), per_cell), random_state=seed)
             for _, g in e.groupby(["country", "department", "job_level"])]
    return pd.concat(parts).sort_values("employee_id").reset_index(drop=True)


def run(subset: pd.DataFrame | None = None) -> dict:
    """The whole model; pass a subset of employees() to run it on a sample."""
    r = roles()
    mk = market(r)
    idx = index_table()
    e = employees(r, mk) if subset is None else subset.reset_index(drop=True)
    bands = current_bands(e)
    gi = grade_index(bands)
    st = structure(e, gi)
    p = positions(e, st, idx)
    return {"roles": r, "market": mk, "lci": idx, "premium_table": premium_table(), "premium": premium(),
            "employees": e, "bands": bands, "grade_index": gi, "raw_index": raw_grade_index(bands), "structure": st, "positions": p,
            "summary": summary(p), "family": by_family(p), "family_premium": family_premium(bands),
            "ads": ads(r, st)}
