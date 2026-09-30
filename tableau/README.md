# Tableau Public: build sheet

The extracts in this folder are written by `src/build_site.py` on every build. They are tidy tables,
one row per observation, ready for Tableau Public (free, no licence needed).

| File | One row per | Key fields |
|---|---|---|
| `structure.csv` | country × grade | min, mid, max in euro and in local currency |
| `positions.csv` | employee on the payroll at 30 June 2026 | family, grade, gender, salary, new range, compa-ratios, status, costs |
| `market.csv` | country × occupation | Eurostat earnings, bonuses, ageing, premium, market pay |
| `job_ads.csv` | role × country | advertised range, annual and monthly |

## Three sheets and a dashboard

1. **Ranges by grade.** `structure.csv`. Rows: `grade`. Columns: a Gantt bar starting at `min` with
   size `max - min`, plus a reference line at `mid`. Filter: `entity` (single value, shown as a
   dropdown). Then drag `positions.csv` onto the same view as a second data source joined on
   `country` and `grade`, and add `salary` as circles, coloured by `status`.
2. **Compa-ratio by family.** `positions.csv`. Rows: `department`. Columns: `AVG(compa_new)`. Colour:
   `entity`. Reference line at 1.
3. **Who moves.** `positions.csv`. Rows: `entity`. Columns: `COUNT(employee_id)` as a percentage of the
   row total, colour: `status`. Add `gender` to rows to see the split the report describes.
4. **Dashboard.** The three sheets, with the `entity` filter applied to all. Title: *From family bands
   to equal-value pay ranges*.

Colours: below the minimum `#2a78d6`, within `#c3c2b7`, above the maximum `#eb6834`: the palette of
the report's charts.

When it is published, add the link to the README next to the report and the range finder.
