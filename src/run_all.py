"""
The whole model in one command:

    python src/run_all.py

roles and market -> grade index and ranges -> every employee's position -> Excel model -> report
and figures -> pay range finder and Tableau extracts. Deterministic: the same inputs give the same
outputs.
"""
import time

import build_report
import build_site
import build_workbook
import model
import report_html


def main() -> None:
    start = time.perf_counter()
    out = model.run()
    m = build_workbook.build(out)
    print(f"workbook -> deliverables/equal_value_pay_ranges.xlsx ({len(m.checks)} reconciliation checks)")
    build_report.write(out)
    report_html.build()
    print("report -> reports/report.md, reports/index.html, reports/figures/")
    build_site.write_site(out)
    build_site.write_tableau(out)
    print("site -> site/ads.html; tableau -> tableau/*.csv")
    print(f"done in {time.perf_counter() - start:.1f}s")


if __name__ == "__main__":
    main()
