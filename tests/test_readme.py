"""The figures quoted in the README are the ones the model produces."""
from pathlib import Path

import build_report as B
import build_workbook
import config as C

ROOT = Path(__file__).resolve().parent.parent
README = (ROOT / "README.md").read_text(encoding="utf-8")
METHOD = (ROOT / "docs" / "method.md").read_text(encoding="utf-8")
NAME = {"IT": "Italy", "PL": "Poland", "DE": "Germany", "ES": "Spain"}


def test_readme_quotes_current_figures(out, tmp_path):
    f = B.facts(out)
    s = f["s"]
    order = s["ratio"].sort_values(ascending=False).index
    it = s.loc["IT"]
    n_checks = len(build_workbook.build(out, tmp_path / "m.xlsx").checks)
    expected = [
        f"Tech's midpoint is {B.pct(f['fp']['D'] - 1)} above Customer Service's",
        f"differ by up to {B.pct(f['fp'].max() - 1)}",
        "payroll is " + B.listing(f"{B.signed(s.loc[c, 'ratio'] - 1)} in {NAME[c]}" for c in order),
        f"Poland at {B.pct(f['current_vs_it']['PL'])} of Italy; the market at {B.pct(f['market_vs_it']['PL'])}",
        f"costs {B.m(f['to_min'], 2)} a year for {f['below']:,} people, {B.pct(f['to_min_women'] / f['to_min'])} of it for women",
        f"In Italy {B.pct(it['below_women'] / it['women'])} of women fall below the minimum against "
        f"{B.pct(it['below_men'] / it['men'])} of men",
        f"{f['above']:,} people sit above their new maximum, {B.m(f['above_max'], 2)} a year, "
        f"{B.pct(s.loc['PL', 'above_max'] / f['above_max'])} of it in Poland",
        f"reconciled on {n_checks:,} checks",
        f"for {f['headcount']:,} employees",
    ]
    missing = [e for e in expected if e not in README]
    assert not missing, f"README is out of date: {missing}"
    assert f"{n_checks:,}\n  checks" in METHOD or f"{n_checks:,} checks" in METHOD, "docs/method.md quotes a stale count"
    assert f"at least {B.pct(C.MIN_PROGRESSION)} per grade" in README
