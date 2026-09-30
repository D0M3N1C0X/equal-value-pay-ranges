"""The pandas model obeys its own definitions: grades, market pricing, the structure and the positions."""
import numpy as np
import pytest

import config as C
import model

APPROX = dict(rel=1e-12, abs=1e-6)


def test_sources_are_the_pinned_ones(monkeypatch):
    model.verify_sources()
    monkeypatch.setattr(C, "EVALUATION_SHA256", "0" * 64)
    with pytest.raises(SystemExit):
        model.verify_sources()


def test_grades_match_the_kit_categories(out):
    r = out["roles"]
    assert len(r) == 36
    weights = sum(C.FACTOR_WEIGHTS.values())
    assert weights == 100
    for t in r.itertuples():
        assert t.points == sum(getattr(t, f) * w for f, w in C.FACTOR_WEIGHTS.items())
        assert t.grade == model.grade_for(t.points)
    assert set(r["isco08"]) <= {"OC1", "OC2", "OC3", "OC4", "OC8", "OC9"}


def test_market_is_base_pay_aged_and_premium(out):
    mk, idx = out["market"], out["lci"]
    for t in mk.itertuples():
        assert t.base == pytest.approx(t.ern - t.bns, **APPROX)
        assert t.local == pytest.approx(t.base * idx.loc[t.country, "aging"] * out["premium"], **APPROX)
        assert t.eur == pytest.approx(t.local / (C.EUR_PLN if t.country == "PL" else 1), **APPROX)
    aging = idx["lci_latest"] / idx["lci_base"] * (idx["lci_latest"] / idx["lci_prev"]) ** C.UPDATE_YEARS
    assert np.allclose(idx["aging"], aging)


def test_premium_is_the_median_of_published_ratios(out):
    t = out["premium_table"]
    assert len(t) == len(C.PREMIUM_COUNTRIES) * len(C.PREMIUM_OCCUPATIONS)
    assert out["premium"] == pytest.approx(t["ratio"].median(), **APPROX)
    assert 1.0 < out["premium"] < 1.2


def test_every_role_is_priced_in_every_country(out):
    e = out["employees"]
    assert e["market"].notna().all() and e["grade"].notna().all()
    assert set(e["country"]) == set(C.ENTITIES)


def test_grade_index_rises_by_at_least_the_minimum_progression(out):
    gi = out["grade_index"]
    assert gi[C.REFERENCE_GRADE] == pytest.approx(1.0)
    steps = gi.values[1:] / gi.values[:-1] - 1
    assert (steps >= C.MIN_PROGRESSION - 1e-12).all()
    assert (gi >= out["raw_index"] - 1e-12).all()


def test_ranges_follow_the_spread_and_rise_with_the_grade(out):
    st = out["structure"]
    assert np.allclose(st["max"] / st["min"] - 1, st["spread"])
    assert np.allclose(st["mid"], (st["min"] + st["max"]) / 2)
    for _, g in st.groupby("country"):
        assert g["min"].is_monotonic_increasing and g["mid"].is_monotonic_increasing and g["max"].is_monotonic_increasing


def test_country_level_reproduces_the_market_for_grades_a_to_e(out):
    e, st = out["employees"], out["structure"].set_index(["country", "grade"])
    for c in C.ENTITIES:
        g = e[(e["country"] == c) & e["grade"].isin(C.LEVEL_GRADES)]
        mids = g["grade"].map(lambda x: st.loc[(c, x), "mid"])
        assert mids.sum() == pytest.approx(C.POSITIONING[c] * g["market"].sum(), rel=1e-12)


def test_polish_ranges_are_above_the_minimum_wage(out):
    st = out["structure"].set_index(["country", "grade"])
    assert st.loc[("PL", "A"), "min_local"] > 4_806 * 12      # 2026 monthly minimum wage, PLN


def test_positions_are_consistent(out):
    p = out["positions"]
    below, above = p["salary"] < p["min"], p["salary"] > p["max"]
    assert ((p["status"] == "Below") == below).all() and ((p["status"] == "Above") == above).all()
    assert np.allclose(p["to_min"], (p["min"] - p["salary"]).clip(lower=0) * p["fte"])
    assert (p.loc[~below, "to_min"] == 0).all() and (p.loc[~above, "above_max"] == 0).all()
    assert (p.loc[above, "years_to_absorb"] > 0).all()
    assert np.allclose(p["compa_new"], p["salary"] / p["mid"])


def test_summary_adds_up(out):
    s, p = out["summary"], out["positions"]
    assert s["headcount"].sum() == len(p)
    assert (s["below"] + s["within"] + s["above"] == s["headcount"]).all()
    assert s["to_min"].sum() == pytest.approx(p["to_min"].sum(), **APPROX)
    assert (s["below_women"] + s["below_men"] == s["below"]).all()


def test_advertised_ranges_contain_the_real_ones(out):
    a, st = out["ads"], out["structure"].set_index(["country", "grade"])
    for t in a.itertuples():
        x = st.loc[(t.country, t.grade)]
        assert t.annual_min <= x["min_local"] <= x["max_local"] <= t.annual_max
        assert t.monthly_min * 12 <= x["min_local"] and t.monthly_max * 12 >= x["max_local"]
        assert t.annual_min % C.AD_STEP[t.currency] == 0 and t.monthly_min % C.AD_MONTHLY_STEP == 0
    assert len(a) == 36 * len(C.ENTITIES)


def test_current_bands_carry_family_premiums_the_new_structure_removes(out):
    fp = out["family_premium"]
    assert (fp["ratio"] > 1.1).all()          # every grade mixes families on different bands today
    st = out["structure"]
    assert st.groupby(["country", "grade"]).size().eq(1).all()   # one range per grade and country


def test_model_runs_on_a_sample():
    o = model.run(model.sample(1, seed=3))
    assert len(o["positions"]) == len(o["employees"])
    assert o["structure"]["mid"].gt(0).all()
