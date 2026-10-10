"""
Tests. Run from the project folder:  python -m pytest -v
The last test starts the real Streamlit app headlessly and checks it renders without errors.
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import analysis  # noqa: E402


@pytest.fixture
def df():
    return pd.DataFrame({
        "country_code": ["NGA", "NGA", "NGA", "GHA", "GHA"],
        "country": ["Nigeria"] * 3 + ["Ghana"] * 2,
        "indicator_code": ["FP.CPI.TOTL.ZG"] * 5,
        "indicator": ["Inflation"] * 5,
        "unit": ["% per year"] * 5,
        "year": [2021, 2022, 2023, 2022, 2023],
        "value": [17.0, 18.8, 24.7, 31.0, 38.0],
    })


def test_latest_with_delta(df):
    year, value, change = analysis.latest_with_delta(df, "NGA", "FP.CPI.TOTL.ZG")
    assert (year, value) == (2023, 24.7)
    assert change == pytest.approx(5.9)                 # approx: floating-point maths isn't exact


def test_latest_missing_returns_none(df):
    assert analysis.latest_with_delta(df, "KEN", "FP.CPI.TOTL.ZG") is None


def test_filter(df):
    out = analysis.filter_data(df, ["NGA"], (2022, 2023))
    assert list(out["year"]) == [2022, 2023]


def test_index_to_first_year(df):
    out = analysis.index_to_first_year(df[df["country_code"] == "GHA"])
    assert list(out["value"].round(1)) == [100.0, 122.6]   # 38 / 31 * 100


def test_ranking_and_insights(df):
    rank = analysis.latest_ranking(df, "FP.CPI.TOTL.ZG")
    assert list(rank["country_code"]) == ["GHA", "NGA"]     # 38.0 > 24.7
    text = " ".join(analysis.insights(df, "FP.CPI.TOTL.ZG"))
    assert "Ghana in 2023" in text and "rose" in text and "2 of 2" in text


def test_bad_source_falls_back_to_demo():
    data, is_demo = analysis.load_data(ROOT / "no-such-file.csv")
    assert is_demo and not data.empty


def test_app_renders_without_errors(monkeypatch):
    from streamlit.testing.v1 import AppTest              # Streamlit's built-in app tester
    monkeypatch.setattr(analysis, "PIPELINE_CSV", str(ROOT / "data" / "demo_indicators.csv"))
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
    assert not at.exception                                # no Python errors while rendering
    assert len(at.metric) == 4                             # the four Nigeria KPI tiles
