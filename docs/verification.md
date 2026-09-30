# Verification register

Every external fact the model relies on, where it comes from and how far it has been checked.
Checked on **30 September 2026**. Not legal or pay advice.

**Status key**

- **Primary** - read in the official text or retrieved from the issuing body.
- **Sources agree** - two or more independent secondary sources say the same.
- **Background** - general knowledge of a standard classification, not re-checked in this session.
- **Judgement** - a choice made for the model, with its reason.
- **Illustrative** - a stated policy assumption. Replace it with the client's own.

## Directive (EU) 2023/970

Statements checked against the Official Journal text in the
[pay-transparency-readiness-kit register](https://github.com/D0M3N1C0X/pay-transparency-readiness-kit/blob/main/docs/verification.md).

| # | Statement used here | Where | Status |
|---|---|---|---|
| P01 | Pay structures compare work of equal value on objective, gender-neutral criteria including skills, effort, responsibility and working conditions | Art. 4(4); kit register V03 | Primary |
| P02 | Applicants get information on the initial pay or its range before the interview; employers may not ask about pay history | Art. 5(1)-(2); kit register V04 | Primary |
| P03 | Criteria for pay, pay levels and progression are made easily accessible to workers | Art. 6; kit register V05 | Primary |
| P04 | Member States transpose by 7 June 2026 | Art. 34(1); kit register V01 | Primary |

## Market data

| # | Figure | Source | Status |
|---|---|---|---|
| P05 | Mean annual gross earnings and annual bonuses by ISCO-08 major group, enterprises with 10+ employees, NACE B–S excluding O, 2022, national currency | Eurostat, [earn_ses22_28](https://ec.europa.eu/eurostat/databrowser/view/earn_ses22_28/default/table); snapshot in `data/raw/eurostat/` | Primary |
| P06 | The same for enterprises of 1,000+ employees (Italy confidential) | Eurostat, [earn_ses22_32](https://ec.europa.eu/eurostat/databrowser/view/earn_ses22_32/default/table) | Primary |
| P07 | Labour cost index, wages and salaries (D11), NACE B–S, 2020 = 100, 2022–2025 | Eurostat, [lc_lci_r2_a](https://ec.europa.eu/eurostat/databrowser/view/lc_lci_r2_a/default/table) | Primary |
| P08 | Euro reference rate, June 2026 monthly average: 4.2568 PLN | ECB Data Portal, series EXR.M.PLN.EUR.SP00.A (see [workforce-cost-model](https://github.com/D0M3N1C0X/workforce-cost-model/blob/main/docs/verification.md), W12) | Primary |
| P09 | Polish minimum wage 2026: 4,806 PLN a month; every Polish range minimum is above it | workforce-cost-model register, W11 | Sources agree |

The address and retrieval date of each snapshot are in `data/raw/eurostat/SOURCES.tsv`.

## Classification and mapping

| # | Statement | Source | Status |
|---|---|---|---|
| P10 | ISCO-08 major groups and the sub-major groups named in `data/isco_map.csv` (42 customer services clerks, 25 ICT professionals, 332 sales and purchasing agents, 2423 personnel and careers professionals, and so on) | ILO, International Standard Classification of Occupations 2008 | Background |
| P11 | Which major group stands in for each of the 36 roles | `data/isco_map.csv`, one rationale per role | Judgement |
| P12 | In Italy and Spain, sector collective agreements set minimum pay by level | General knowledge of both systems | Background |

## Policy assumptions

| # | Assumption | Value | Status |
|---|---|---|---|
| P13 | Positioning of the midpoint against the large-employer market | 100% in every country | Illustrative |
| P14 | Range spread by grade | 30% (A–C), 40% (D–E), 50% (F), 60% (G) | Illustrative |
| P15 | Minimum progression between midpoints | 8% | Illustrative |
| P16 | Grades used to set the country level | A–E | Judgement |
| P17 | Update from 2025 to mid-2026 | half a year at the 2025 labour cost growth | Illustrative |
| P18 | Rounding of advertised ranges; Poland advertises monthly pay | €500 / PLN 1,000 a year, PLN 100 a month | Illustrative |
| P19 | Employees, salaries, current bands and job evaluation scores | synthetic, from hr-people-analytics and the kit | Illustrative |
