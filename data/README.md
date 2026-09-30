# Data

| File | Made by | What it is |
|---|---|---|
| `source/employees.csv` | copied from [hr-people-analytics](https://github.com/D0M3N1C0X/hr-people-analytics) at commit `201495b` | The synthetic 4,000-employee organisation, with each employee's current band midpoint. SHA-256 `3727232…7da79c`, pinned in `src/config.py` and checked on every build. |
| `source/job_evaluation.csv` | copied from [pay-transparency-readiness-kit](https://github.com/D0M3N1C0X/pay-transparency-readiness-kit) at commit `e0c7bef` | 36 roles scored on the four Article 4(4) criteria, with a rationale per role. SHA-256 `7c4b4ee…628b0`, pinned. |
| `isco_map.csv` | written by hand | The ISCO-08 major group that stands in for each role in the market, with a rationale. |
| `raw/eurostat/*.json` | `src/fetch_eurostat.py` | Snapshots of the Eurostat API responses (JSON-stat 2.0). `SOURCES.tsv` records each address and retrieval date. The pipeline reads only these files. |

Employees and bands are synthetic: no real person's pay is in this repository. Market figures are
real and public.

## Columns the model reads from `source/employees.csv`

| Column | Used as |
|---|---|
| `employee_id`, `country`, `department`, `job_level`, `gender`, `fte` | who, where, which role |
| `base_salary_eur` | full-time annual base pay |
| `salary_band_mid_eur` | the current band midpoint for the employee's country, family and level |
| `hire_date`, `exit_date` | on the payroll on 30 June 2026 |
