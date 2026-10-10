"""
analysis.py  -  Data loading and the numbers behind the dashboard.
Kept separate from app.py (the Streamlit page) so it can be unit-tested without a browser.
"""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent

# Clean data published every week by the ETL pipeline project (GitHub Actions commits this file).
PIPELINE_CSV = ("https://raw.githubusercontent.com/Bak-AbasiUdoessien/"
                "ng-economic-data-pipeline/main/data/exports/indicators.csv")
DEMO_CSV = ROOT / "data" / "demo_indicators.csv"      # MADE-UP data, used only if the real file can't be read

REQUIRED = {"country_code", "country", "indicator_code", "indicator", "unit", "year", "value"}

# Colour follows the COUNTRY, never its position - so filtering never repaints a line.
# (Categorical palette validated for colour-blind separation; see README.)
COUNTRY_COLOURS = {"NGA": "#2a78d6", "GHA": "#eb6834", "KEN": "#1baf7a", "ZAF": "#eda100", "EGY": "#e87ba4"}

# For these indicators a RISE is bad news (shown red in the KPI tiles).
HIGHER_IS_WORSE = {"FP.CPI.TOTL.ZG", "PA.NUS.FCRF", "SL.UEM.TOTL.ZS"}

# Exchange rates are in different currencies (naira, cedi, shilling...), so raw values can't share an axis.
INDEX_ONLY = {"PA.NUS.FCRF"}


def load_data(source=PIPELINE_CSV):
    """
    Read the pipeline's CSV. Returns (DataFrame, is_demo).
    Falls back to the bundled demo file if the real one can't be downloaded or looks wrong.
    """
    try:
        df = pd.read_csv(source)                          # pandas can read straight from a URL
        missing = REQUIRED - set(df.columns)              # set difference: required columns not present
        if missing or df.empty:
            raise ValueError(f"unexpected file (missing {missing})")
        return df, False
    except Exception:                                     # network down, file not published yet, etc.
        return pd.read_csv(DEMO_CSV), True


def filter_data(df, countries, years):
    """Rows for the chosen countries and the inclusive (first, last) year range."""
    first, last = years
    return df[df["country_code"].isin(countries) & df["year"].between(first, last)]


def latest_with_delta(df, country, indicator):
    """
    Most recent value and its change from the previous available year.
    Returns (year, value, change) or None if there is no data.
    """
    s = df[(df["country_code"] == country) & (df["indicator_code"] == indicator)].sort_values("year")
    if s.empty:
        return None
    last = s.iloc[-1]                                     # .iloc[-1] = last row
    change = last["value"] - s.iloc[-2]["value"] if len(s) > 1 else None
    return int(last["year"]), float(last["value"]), change


def index_to_first_year(df):
    """Rescale each country's series so its first year = 100 (makes different currencies comparable)."""
    df = df.sort_values("year").copy()
    first = df.groupby("country_code")["value"].transform("first")   # each row gets its country's first value
    df["value"] = df["value"] / first * 100
    return df


def latest_ranking(df, indicator):
    """Each country's latest value for an indicator, highest first."""
    s = df[df["indicator_code"] == indicator].sort_values("year")
    latest = s.groupby("country_code").tail(1)            # last row per country
    return latest.sort_values("value", ascending=False).reset_index(drop=True)


def insights(df, indicator):
    """A few plain-English sentences about the selected data (what a reader should notice)."""
    s = df[df["indicator_code"] == indicator]
    if s.empty:
        return []
    name, unit = s["indicator"].iloc[0], s["unit"].iloc[0]
    out = []
    peak = s.loc[s["value"].idxmax()]                     # idxmax = row label of the largest value
    out.append(f"Highest {name.lower()} in the selection: **{peak['country']} in {int(peak['year'])}** "
               f"({peak['value']:,.1f} {unit}).")
    ngr = s[s["country_code"] == "NGA"].sort_values("year")
    if len(ngr) >= 2:
        first, last = ngr.iloc[0], ngr.iloc[-1]
        direction = "rose" if last["value"] > first["value"] else "fell"
        out.append(f"Nigeria's {name.lower()} {direction} from {first['value']:,.1f} in {int(first['year'])} "
                   f"to {last['value']:,.1f} in {int(last['year'])}.")
        if indicator not in INDEX_ONLY:
            rank = latest_ranking(s, indicator)
            pos = rank.index[rank["country_code"] == "NGA"]
            if len(pos):
                out.append(f"In the latest year Nigeria ranks **{pos[0] + 1} of {len(rank)}** "
                           f"countries shown (1 = highest).")
    return out
