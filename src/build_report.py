"""
Writes reports/report.md and its figures: the read-out for an HR director or head of reward.
Every figure comes from model.run(), the same results the workbook reconciles against.
"""
import pandas as pd

import charts
import config as C
import model

FIG = C.REPORTS / "figures"
KIT = C.KIT_REPO
COUNTRY = {"IT": "Italy", "PL": "Poland", "DE": "Germany", "ES": "Spain"}


def m(x, d=1):
    return f"{'−' if x < 0 else ''}€{abs(x) / 1e6:,.{d}f}M"


def k(x):
    return f"€{x / 1e3:,.0f}k"


def pct(x, d=0):
    return f"{'−' if x < 0 else ''}{abs(x) * 100:.{d}f}%"


def signed(x, d=1):
    return f"{'+' if x >= 0 else '−'}{abs(x) * 100:.{d}f}%"


def money(x, cur):
    return f"{'€' if cur == 'EUR' else 'PLN '}{x:,.0f}"


def table(head, rows, align):
    out = ["| " + " | ".join(head) + " |", "|" + "|".join("---:" if a == "r" else "---" for a in align) + "|"]
    return "\n".join(out + ["| " + " | ".join(str(c) for c in r) + " |" for r in rows])


def listing(items):
    items = list(items)
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


def facts(o: dict) -> dict:
    s = o["summary"].set_index("country")
    st = o["structure"].set_index(["country", "grade"])
    b = o["bands"]
    anchor = b[(b["department"] == "Customer Service") & (b["job_level"] == "L1")].set_index("country")["band_mid"]
    level = st.xs(C.REFERENCE_GRADE, level="grade")["level"]
    fp = o["family_premium"].groupby("grade")["ratio"].max()
    widest = fp.idxmax()
    w = b[(b["country"] == "IT") & (b["grade"] == widest)].merge(o["roles"][["department", "job_level", "points"]],
                                                                 on=["department", "job_level"])
    top, bottom = w.loc[w["band_mid"].idxmax()], w.loc[w["band_mid"].idxmin()]
    p = o["positions"]
    women = p.groupby("department")["gender"].apply(lambda g: (g == "F").mean())
    above = p[p["status"] == "Above"]
    return {
        "s": s, "st": st, "fam": o["family"], "fp": fp,
        "current_vs_it": anchor / anchor["IT"], "market_vs_it": level / level["IT"],
        "headcount": int(s["headcount"].sum()),
        "to_min": s["to_min"].sum(), "to_min_women": s["to_min_women"].sum(),
        "below": int(s["below"].sum()), "above": int(s["above"].sum()), "above_max": s["above_max"].sum(),
        "years": above.groupby("country")["years_to_absorb"].median(),
        "premium": o["premium"], "grade_index": o["grade_index"], "raw_index": o["raw_index"],
        "lci": o["lci"], "widest": widest, "top": top, "bottom": bottom, "women": women,
    }


def pl_positioning(levels=(1.0, 1.1, 1.2)) -> list:
    """Poland's positions under other positioning policies, everything else unchanged."""
    keep = C.POSITIONING["PL"]
    rows = []
    try:
        for pos in levels:
            C.POSITIONING["PL"] = pos
            t = model.run()["summary"].set_index("country").loc["PL"]
            rows.append((pos, t["below"] / t["headcount"], t["above"] / t["headcount"], t["above_max"], t["to_min"]))
    finally:
        C.POSITIONING["PL"] = keep
    return rows


def write(o: dict) -> dict:
    f = facts(o)
    s, st, fam = f["s"], f["st"], f["fam"]
    names = C.ENTITIES
    FIG.mkdir(parents=True, exist_ok=True)

    rows = [(names[c], s.loc[c, "ratio"]) for c in names]
    hi_c = s["ratio"].idxmax()
    lo_c = s["ratio"].idxmin()
    (FIG / "01_market_position.svg").write_text(charts.market_position(
        rows, f"One pay scale, four markets: {names[hi_c].split(' · ')[1]} {signed(s.loc[hi_c, 'ratio'] - 1)}, "
              f"{names[lo_c].split(' · ')[1]} {signed(s.loc[lo_c, 'ratio'] - 1)}",
        "Payroll against what large employers pay for the same occupations, grades A–E, mid-2026"))
    fam_rows = [(d, [fam.loc[d, c] for c in names]) for d in C.DEPARTMENTS]
    tech, cs = fam.loc["Tech"], fam.loc["Customer Service"]
    (FIG / "02_family_compa.svg").write_text(charts.family_compa(
        fam_rows, f"Without family premiums, Tech sits {pct(tech.min() - 1)}–{pct(tech.max() - 1)} above the midpoint",
        "Average compa-ratio against the new equal-value midpoint, by family: dot = mean of the four countries, "
        "line = their range"))
    b = o["bands"]
    it_rows = []
    for _, g in C.GRADES:
        x = st.loc[("IT", g)]
        cur = [(f"{r.department} {r.job_level}", r.band_mid) for r in b[(b["country"] == "IT") & (b["grade"] == g)]
               .sort_values("band_mid").itertuples()]
        it_rows.append((g, x["min"], x["mid"], x["max"], cur))
    (FIG / "03_ranges_italy.svg").write_text(charts.ranges(
        it_rows, "Italy: one range per grade where there were up to six family bands",
        "New range by grade (full-time annual base pay) and the current midpoint of each role in the grade"))
    pos_rows = [(names[c], s.loc[c, "below"] / s.loc[c, "headcount"], s.loc[c, "within"] / s.loc[c, "headcount"],
                 s.loc[c, "above"] / s.loc[c, "headcount"]) for c in names]
    (FIG / "04_positions.svg").write_text(charts.positions(
        pos_rows, f"{pct(s.loc['PL', 'above'] / s.loc['PL', 'headcount'])} of Poland above the new maximum, "
                  f"{pct(s.loc['DE', 'below'] / s.loc['DE', 'headcount'])} of Germany below the minimum",
        "Employees on the payroll at 30 June 2026 against the range of their grade"))

    women_share = f["to_min_women"] / f["to_min"]
    it_w = s.loc["IT", "below_women"] / s.loc["IT", "women"]
    it_m = s.loc["IT", "below_men"] / s.loc["IT", "men"]
    pl_share = s.loc["PL", "above_max"] / f["above_max"]
    fp = f["fp"]
    widest = fp.idxmax()
    ads = o["ads"].set_index(["role", "country"])

    L = []
    add = L.append
    add("# From family bands to equal-value pay ranges")
    add("")
    add(f"**Scope:** {listing(names.values())}; {f['headcount']:,} employees on the payroll at 30 June 2026, "
        f"36 roles in six families")
    add(f"**Market:** Eurostat Structure of Earnings Survey 2022 by occupation, aged to mid-2026 with the labour cost "
        f"index, plus a {pct(f['premium'] - 1, 1)} large-employer premium")
    add(f"**Data:** employees and current bands synthetic, from [hr-people-analytics]({C.SOURCE_REPO}); job evaluation "
        f"from [pay-transparency-readiness-kit]({KIT}); market figures real, with their sources in "
        f"[docs/verification.md](../docs/verification.md)")
    add("")
    add("> The Pay Transparency Directive asks for pay structures that compare work of equal value on objective, "
        "gender-neutral criteria (Article 4), a pay range for every vacancy (Article 5) and accessible criteria for "
        "pay and progression (Article 6). This review tests the company's bands against all three. Not legal advice.")
    add("")

    add("## The answer")
    add("")
    top, bottom = f["top"], f["bottom"]
    add(f"- **The current bands pay the family, not the job.** At the same level, Tech's midpoint is "
        f"{pct(fp['D'] - 1)} above Customer Service's. Inside grade {widest}, {top['department']} {top['job_level']} "
        f"({top['points']:.0f} points) has a midpoint {pct(top['band_mid'] / bottom['band_mid'] - 1)} above "
        f"{bottom['department']} {bottom['job_level']} ({bottom['points']:.0f} points). The evaluation gives no reason "
        f"for the difference; if the company keeps it, it needs a documented one.")
    add(f"- **One pay scale, four markets.** Against large employers for the same occupations, payroll is "
        + listing(f"{signed(s.loc[c, 'ratio'] - 1)} in {COUNTRY[c]}" for c in
                  s["ratio"].sort_values(ascending=False).index)
        + f". The bands put Poland at {pct(f['current_vs_it']['PL'])} of Italy; the market puts it at "
          f"{pct(f['market_vs_it']['PL'])}.")
    add(f"- **Bringing everyone to the new minimum costs {m(f['to_min'], 2)} a year for {f['below']:,} people, "
        f"{pct(women_share)} of it for women.** In Italy {pct(it_w)} of women fall below the minimum against "
        f"{pct(it_m)} of men. The families the bands pay least employ more women: Customer Service is "
        f"{pct(f['women']['Customer Service'])} women and HR {pct(f['women']['HR'])}, Tech {pct(f['women']['Tech'])}.")
    add(f"- **{f['above']:,} people are paid above their new maximum, {m(f['above_max'], 2)} a year, "
        f"{pct(pl_share)} of it in Poland.** Their pay is protected, not cut; at Polish wage growth the ranges catch "
        f"up in about {f['years']['PL']:.1f} years.")
    add(f"- **Every role now has a range to advertise.** Customer Service L1: "
        f"{ads.loc[('Customer Service L1', 'IT'), 'text'].replace(', full time', '')} in Italy, "
        f"{ads.loc[('Customer Service L1', 'PL'), 'text'].replace(', full time', '')} in Poland. "
        f"All 144 are in [the workbook](../deliverables/equal_value_pay_ranges.xlsx) and the "
        f"[range finder](../site/ads.html).")
    add("")

    add("## 1. How the current bands are built")
    add("")
    add("Each band midpoint is a country factor times a family premium times a level step. At every level the "
        "premium is the same:")
    add("")
    premium_rows = []
    it_l3 = b[(b["country"] == "IT") & (b["job_level"] == "L3")].set_index("department")["band_mid"]
    for d in C.DEPARTMENTS:
        premium_rows.append([d, k(it_l3[d]), signed(it_l3[d] / it_l3["Customer Service"] - 1, 0),
                             pct((o["positions"]["department"] == d).mean()),
                             pct((o["positions"].loc[o["positions"]["department"] == d, "gender"] == "F").mean())])
    add(table(["Family", "Italy L3 midpoint", "vs Customer Service", "Share of staff", "Women"], premium_rows,
              "lrrrr"))
    add("")
    add("The job evaluation scores the four Article 4(4) criteria (skills, effort, responsibility, working "
        "conditions) and groups roles into seven grades of equal value. Customer Service and Operations score high on "
        "effort and working conditions, which the family premiums ignore.")
    add("")
    add("![Italy: current midpoints and new ranges](figures/03_ranges_italy.svg)")
    add("")

    add("## 2. The market, country by country")
    add("")
    add(f"Each role is matched to an ISCO major group (a contact centre agent to clerical support workers, a Tech L3 "
        f"to professionals) and priced on Eurostat's mean base pay for that group: earnings minus annual bonuses, "
        f"aged from 2022 with the labour cost index for wages and salaries, and raised by "
        f"{pct(f['premium'] - 1, 1)}, what enterprises of 1,000+ pay over enterprises of 10+ in Germany, Spain and "
        f"Poland (Italy's figure is confidential).")
    add("")
    add("![Payroll against market](figures/01_market_position.svg)")
    add("")
    add(table(["Entity", "Payroll against market", "Current bands vs Italy", "Market vs Italy",
               "Labour cost growth, 2025"],
              [[names[c], signed(s.loc[c, "ratio"] - 1), pct(f["current_vs_it"][c]), pct(f["market_vs_it"][c]),
                pct(f["lci"].loc[c, "growth"], 1)] for c in names], "lrrrr"))
    add("")
    add("*Grades A–E only: ISCO group 1 averages every manager, from a shop manager to an Italian dirigente, so it is "
        "not a fair yardstick for grades F and G.*")
    add("")

    add("## 3. The new structure")
    add("")
    add("One range per grade and country. The **midpoint** is the country's market level times a grade index: the "
        "progression between grades in today's bands, with the family premiums averaged out and each grade at least "
        f"{pct(C.MIN_PROGRESSION)} above the one below. The **range** runs from {pct(C.SPREAD['A'])} wide at grade A "
        f"to {pct(C.SPREAD['G'])} at grade G.")
    add("")
    grade_rows = []
    for _, g in C.GRADES:
        row = [g, f"{f['grade_index'][g]:.2f}"]
        for c in names:
            x = st.loc[(c, g)]
            cur = C.CURRENCY[c]
            row.append(f"{x['min_local']:,.0f} – {x['max_local']:,.0f}")
        grade_rows.append(row)
    add(table(["Grade", "Index", *[names[c] for c in names]], grade_rows, "lrrrrr"))
    add("")
    add("*Full-time annual base pay: euro, Poland in zloty. The grade index is 1 at grade D.*")
    add("")

    add("## 4. Who moves")
    add("")
    add("![Positions against the new ranges](figures/04_positions.svg)")
    add("")
    add(table(["Entity", "Below minimum", "Above maximum", "Cost to minimum", "of which women", "Pay above maximum",
               "Years to absorb"],
              [[names[c], f"{int(s.loc[c, 'below']):,}", f"{int(s.loc[c, 'above']):,}", m(s.loc[c, "to_min"], 2),
                pct(s.loc[c, "to_min_women"] / s.loc[c, "to_min"]) if s.loc[c, "to_min"] else "-",
                m(s.loc[c, "above_max"], 2), f"{f['years'][c]:.1f}"] for c in names], "lrrrrrr"))
    add("")
    add("*Costs are annual full-time-equivalent base pay, before employer contributions. Years to absorb: the median "
        "time for the maximum to reach a frozen salary at the country's 2025 labour cost growth.*")
    add("")
    add("![Compa-ratio by family](figures/02_family_compa.svg)")
    add("")
    pl = pl_positioning()
    add(f"Poland's position is a policy choice the company never made explicitly. Setting its midpoints above the "
        f"local market changes the picture:")
    add("")
    add(table(["Poland positioned at", "Below minimum", "Above maximum", "Pay above maximum", "Cost to minimum"],
              [[pct(pos), pct(bl), pct(ab), m(ex, 2), m(tm, 2)] for pos, bl, ab, ex, tm in pl], "lrrrr"))
    add("")
    add("*The wider the positioning, the more staff fall below the minimum instead: Polish pay is dispersed more "
        "widely than a single range can hold.*")
    add("")

    add("## 5. Job advertisements and progression")
    add("")
    add("Article 5 gives applicants the right to the starting pay or its range before the interview, based on "
        "objective, gender-neutral criteria, and bars employers from asking about pay history. The range for each "
        "role follows from its grade:")
    add("")
    sample_roles = ["Customer Service L1", "Operations L2", "Tech L3", "Finance L4", "Sales L5"]
    add(table(["Role", "Grade", *[names[c] for c in names]],
              [[r_, ads.loc[(r_, "IT"), "grade"], *[ads.loc[(r_, c), "text"].replace(" gross", "").replace(", full time", "")
                                                   for c in names]] for r_ in sample_roles], "llllll"))
    add("")
    add("Rounded outwards to €500 or PLN 1,000 a year (PLN 100 a month), so the published range always contains "
        "the real one. Poland advertises monthly gross pay, as its job market does; the others annual. Article 6 then "
        "asks for the criteria that move someone through the range: the proposal is time in grade and performance "
        "against the role's objectives, with position in range reviewed each year.")
    add("")

    add("## 6. Recommendations")
    add("")
    add("1. **Adopt one structure by grade.** Keep a family premium only where the company can document an objective, "
        "gender-neutral market reason, review it every year, and have counsel test it against national law.")
    add(f"2. **Close the gaps to the minimum over two pay reviews**, starting with the grades where women are furthest "
        f"below: {m(f['to_min'], 2)} a year in total.")
    add("3. **Protect pay above the maximum, don't cut it.** Hold increases to lump sums until the range catches up, "
        "and say so in writing to the people affected.")
    add("4. **Decide Poland's positioning deliberately.** Paying above the local market can be a sound retention choice "
        "in Kraków; it should be a decision with a number, not the side-effect of a single scale.")
    add("5. **Publish ranges in every vacancy** in the countries that have transposed Article 5, and remove "
        "pay-history questions from applications and interviews.")
    add("6. **Price the jobs on a salary survey before implementing.** Eurostat gives reliable country levels by "
        "occupation, not level-by-level market rates.")
    add("")

    add("## 7. Method and limits")
    add("")
    add("- **Two engines, one answer.** Every figure is computed in pandas and again by live formulas in "
        "[the workbook](../deliverables/equal_value_pay_ranges.xlsx); its Reconciliation sheet checks each pair, and CI "
        "recalculates the workbook with LibreOffice.")
    add("- **Occupations, not jobs.** ISCO major groups are broad and earnings are means, which sit above medians. "
        "The market sets each country's level; it cannot price the step from team lead to manager.")
    add("- **Synthetic company.** Employees, salaries and current bands come from a synthetic organisation, whose "
        "country pay levels were set without reference to the market; the gap to the market is part of the case.")
    add("- **Collective agreements.** In Italy and Spain sector agreements set minimum pay by level; any range sits "
        "on top of them. Full method in [docs/method.md](../docs/method.md).")
    add("")
    (C.REPORTS / "report.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    return f


def main() -> None:
    write(model.run())
    import report_html
    report_html.build()
    print("report -> reports/report.md, reports/index.html, 4 figures")


if __name__ == "__main__":
    main()
