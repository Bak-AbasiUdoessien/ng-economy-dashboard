"""
make_demo_data.py  -  Writes data/demo_indicators.csv: MADE-UP numbers in the same format
as the pipeline's real export. Only used when the live data can't be loaded.
"""

import random
from pathlib import Path

import pandas as pd

COUNTRIES = {"NGA": "Nigeria", "GHA": "Ghana", "KEN": "Kenya", "ZAF": "South Africa", "EGY": "Egypt"}
INDICATORS = {   # code: (name, unit, invented starting level, invented yearly drift)
    "FP.CPI.TOTL.ZG": ("Inflation", "% per year", 10, 1.02),
    "NY.GDP.MKTP.KD.ZG": ("GDP growth", "% per year", 5, 0.98),
    "NY.GDP.PCAP.CD": ("GDP per person", "current US$", 1500, 1.04),
    "PA.NUS.FCRF": ("Official exchange rate", "local currency per US$", 100, 1.08),
    "SL.UEM.TOTL.ZS": ("Unemployment", "% of labour force", 8, 1.01),
    "BX.TRF.PWKR.CD.DT": ("Remittances received", "current US$", 2e9, 1.06),
}


def main():
    rnd = random.Random(7)
    rows = []
    for code, (name, unit, start, drift) in INDICATORS.items():
        for iso, country in COUNTRIES.items():
            value = start * rnd.uniform(0.5, 1.5)
            for year in range(2000, 2025):
                value *= drift * rnd.uniform(0.93, 1.07)              # a random walk around the drift
                rows.append([iso, country, code, name, unit, year, round(value, 3)])
    df = pd.DataFrame(rows, columns=["country_code", "country", "indicator_code", "indicator", "unit", "year", "value"])
    out = Path(__file__).parent / "data" / "demo_indicators.csv"
    df.to_csv(out, index=False)
    print(f"wrote {len(df)} MADE-UP rows -> {out.name}")


if __name__ == "__main__":
    main()
