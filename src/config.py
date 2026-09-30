"""
Every assumption the model uses, in one place, with its source. The workbook's Settings sheet is
written from this file, so the Python pipeline and the Excel model start from the same numbers.
"""
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SOURCE_EMPLOYEES = DATA / "source" / "employees.csv"
SOURCE_EVALUATION = DATA / "source" / "job_evaluation.csv"
ISCO_MAP = DATA / "isco_map.csv"
EUROSTAT = DATA / "raw" / "eurostat"
DELIVERABLES = ROOT / "deliverables"
REPORTS = ROOT / "reports"
TABLEAU = ROOT / "tableau"
SITE = ROOT / "site"

# The organisation analysed in hr-people-analytics, and the job evaluation scored in
# pay-transparency-readiness-kit: same files, pinned by checksum.
SOURCE_REPO = "https://github.com/D0M3N1C0X/hr-people-analytics"
SOURCE_COMMIT = "201495b"
SOURCE_SHA256 = "372723241e92aa3d233c9298f8a0d2e713e72ff8f0c989e24a7bf743fc7da79c"
KIT_REPO = "https://github.com/D0M3N1C0X/pay-transparency-readiness-kit"
KIT_COMMIT = "e0c7bef"
EVALUATION_SHA256 = "7c4b4ee03db9481893374b9100c8b4a75c4a44b1688b20f9b726df2874c628b0"

SNAPSHOT = date(2026, 6, 30)          # workers on the payroll that day, as in the kit
ENTITIES = {"IT": "IT · Milan", "PL": "PL · Kraków", "DE": "DE · Munich", "ES": "ES · Barcelona"}
DEPARTMENTS = ["Customer Service", "Operations", "Tech", "Sales", "Finance", "HR"]
LEVELS = ["L1", "L2", "L3", "L4", "L5", "L6"]

# ---- Job evaluation (as in the kit) -----------------------------------------------------------
FACTORS = ["skills", "effort", "responsibility", "working_conditions"]
FACTOR_WEIGHTS = {"skills": 35, "effort": 15, "responsibility": 35, "working_conditions": 15}
# Grades are the kit's categories of workers of equal value: point bands, lower limit inclusive.
GRADES = [(100, "A"), (160, "B"), (200, "C"), (250, "D"), (300, "E"), (340, "F"), (400, "G")]
REFERENCE_GRADE = "D"

# ---- Market: Eurostat Structure of Earnings Survey 2022 ------------------------------------------
# Mean annual gross earnings by occupation (ISCO-08 major group), enterprises with 10+ employees,
# NACE B-S excluding O (earn_ses22_28). Base pay = earnings minus annual bonuses (indicator BNS).
# Values in national currency, so Poland is priced in zloty.
MARKET_TABLE = "earn_ses22_28"
SIZE_TABLE = "earn_ses22_32"          # same, by enterprise size class
INDEX_TABLE = "lc_lci_r2_a"           # labour cost index, wages and salaries (D11), NACE B-S, 2020=100
MARKET_YEAR = 2022
INDEX_LATEST = 2025
# Large-employer premium: the entities employ 500-1,200 people. Eurostat publishes earnings for
# enterprises of 1,000+ for Germany, Spain and Poland but not Italy (confidential), so one premium,
# the median ratio of 1,000+ to 10+ earnings over these occupations, applies to all four.
PREMIUM_COUNTRIES = ["DE", "ES", "PL"]
PREMIUM_OCCUPATIONS = ["OC1", "OC2", "OC3", "OC4"]
# From 2025 to the snapshot: half a year at each country's 2024-2025 growth. Illustrative.
UPDATE_YEARS = 0.5

EUR_PLN = 4.2568                      # ECB euro reference rate, monthly average June 2026
CURRENCY = {"IT": "EUR", "PL": "PLN", "DE": "EUR", "ES": "EUR"}

# ---- Pay policy (the client's choices; illustrative defaults) --------------------------------------
POSITIONING = {"IT": 1.00, "PL": 1.00, "DE": 1.00, "ES": 1.00}   # midpoint vs large-employer market
# The country level is set on the non-managerial grades: ISCO major group 1 puts every manager in one
# average, from a shop manager to an Italian dirigente, so it is a poor yardstick for grades F and G,
# which follow the grade index instead.
LEVEL_GRADES = ["A", "B", "C", "D", "E"]
# Each grade's midpoint at least this much above the one below. Grades cut across job levels, so
# the current bands alone can leave two adjacent grades almost level (B and C here).
MIN_PROGRESSION = 0.08
# Range spread (maximum / minimum - 1) by grade: narrower at entry grades, wider at the top.
SPREAD = {"A": 0.30, "B": 0.30, "C": 0.30, "D": 0.40, "E": 0.40, "F": 0.50, "G": 0.60}

# ---- Job advertisements (Article 5) ------------------------------------------------------------------
AD_STEP = {"EUR": 500, "PLN": 1000}   # annual ranges rounded outwards to this step
AD_MONTHLY_STEP = 100                 # Poland advertises monthly gross pay, rounded outwards
AD_PERIOD = {"IT": "year", "PL": "month", "DE": "year", "ES": "year"}
