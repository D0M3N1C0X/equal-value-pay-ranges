# Method

How every number is produced. The same rules are written twice, in pandas
([`src/model.py`](../src/model.py)) and as live formulas in the workbook
([`src/build_workbook.py`](../src/build_workbook.py)), and the Reconciliation sheet checks that
the two agree. Sources and their status are in [verification.md](verification.md).

## Population

| Choice | This model | Why |
|---|---|---|
| Employers | The four entities of the organisation in hr-people-analytics: Milan, Kraków, Munich, Barcelona | The same organisation as pay-transparency-readiness-kit and workforce-cost-model. |
| Who counts | Everyone on the payroll on 30 June 2026 | The snapshot the kit uses. |
| Pay | Full-time annual base pay, in euro; part-timers are compared on their full-time salary and costed at their FTE | Ranges are set for full-time jobs, as they are advertised. |
| Current bands | The midpoint recorded against each employee in the HRIS (`salary_band_mid_eur`): one per country, family and level | It is the structure the company runs today. |

## 1. Grades: work of equal value

Each of the 36 roles (six families × six levels) is scored 1–5 on skills, effort, responsibility and
working conditions, the criteria in Article 4(4), with weights 35/15/35/15 so a role scores 100–500
points. Seven point bands, the kit's categories of workers, become the grades A–G. The scores and
their rationale are the kit's (`data/source/job_evaluation.csv`, pinned by checksum); this model does
not re-score them.

Grades cut across levels: a Customer Service L1 (175 points) and a Tech L2 (185) share grade B.

## 2. The market

For each role an **ISCO-08 major group** stands in for the market (`data/isco_map.csv`, with a
rationale per role): contact centre agents are clerical support workers (OC4), Tech L3 is
professionals (OC2), managers are OC1, and so on. For each group and country:

| Step | Rule | Source |
|---|---|---|
| Earnings | Mean annual gross earnings, enterprises with 10+ employees, NACE B–S excluding O, 2022, national currency | earn_ses22_28 |
| Base pay | Earnings minus annual bonuses (indicator BNS) | earn_ses22_28 |
| To mid-2026 | × labour cost index 2025 / 2022 × (2025 / 2024)<sup>½</sup>: wages and salaries, NACE B–S | lc_lci_r2_a |
| Large employers | × 1 + premium, where the premium is the median ratio of earnings in enterprises of 1,000+ to 10+ over OC1–OC4 in Germany, Spain and Poland | earn_ses22_32 |
| Euro | Polish zloty ÷ 4.2568 | ECB, June 2026 average |

Italy's 1,000+ earnings are confidential, so one premium applies to all four countries.

## 3. The grade index: the shape of the structure

Eurostat publishes occupations, not levels, so it cannot say how much a grade E job earns over a
grade D job. The shape comes from the company's own bands, with the family premiums removed:

1. For each country and grade, the geometric mean of the band midpoints of the roles in the grade
   (every family counts once, whatever its headcount).
2. Divided by the same figure for grade D; the ratios averaged across countries, geometrically.
3. Each grade then kept at least 8% above the one below: because grades cut across levels, grade B
   (with Tech and Finance L2) sits almost level with grade C in the current bands.

## 4. The country level and the ranges

- **Level.** For each country, level = positioning × Σ market pay ÷ Σ grade index, over the employees
  in grades A–E. The new midpoints of today's non-managerial workforce then add up to what large
  employers pay for the same occupations. Grades F and G are left out of the fit because ISCO group 1
  averages every manager, from a shop manager to an Italian *dirigente*.
- **Midpoint** = level × grade index.
- **Range.** Spread s by grade (30% for A–C, 40% for D–E, 50% for F, 60% for G): minimum = midpoint ×
  2 / (2 + s), maximum = minimum × (1 + s), so the midpoint sits halfway.
- **Positioning** is 100% for every country: a policy the client sets, and the lever the report tests
  for Poland.

## 5. Positions and costs

| Measure | Rule |
|---|---|
| Compa-ratio, current | salary ÷ current band midpoint |
| Compa-ratio, new | salary ÷ new midpoint |
| Status | Below if salary < minimum; Above if salary > maximum; otherwise Within |
| Cost to minimum | (minimum − salary) × FTE, for those below; annual base pay, before employer contributions |
| Pay above maximum | (salary − maximum) × FTE, for those above |
| Years to absorb | ln(salary ÷ maximum) ÷ ln(1 + the country's 2025 labour cost growth): how long a frozen salary takes to re-enter a range that moves with the market |
| Payroll against market | Σ salary ÷ Σ market pay, grades A–E |

## 6. Job advertisements

The range for a role in a country is its grade's range in local currency, rounded outwards (to €500 or
PLN 1,000 a year, PLN 100 a month) so the published range always contains the real one. Poland shows
monthly gross pay, the convention of its job market; the others annual. The text follows one pattern:
"EUR 27,500 – 36,000 gross per year, full time".

## Two engines, one answer

- The workbook holds no pasted results except the Python column of the Reconciliation sheet: 1,315
  checks, from the Eurostat inputs to every advertised range and its text. A value matches within 1
  part in 10⁹.
- CI recalculates the full workbook with LibreOffice and fails on any mismatch or formula error. The
  test suite calculates a sample workbook (two employees per country, family and level) with the
  pure-Python `formulas` package, and checks that a changed value is caught.

## Limits

- **Occupations, not jobs.** ISCO major groups are broad and SES earnings are means, which sit above
  medians. The market sets each country's level for the company's mix of occupations; it cannot price
  a specific job or the step from team lead to manager. A real engagement matches jobs and levels to a
  salary survey.
- **Sector.** Earnings cover NACE B–S excluding O, all industries together.
- **Synthetic company.** Employees, salaries and current bands are synthetic. Their country pay
  levels were set without reference to the market, which is part of the case the report makes.
- **Collective agreements.** In Italy and Spain sector agreements set minimum pay by level; the ranges
  must sit on top of them. Not modelled.
- **Base pay only.** Bonus, commission and allowances are outside the ranges; the kit covers them.
