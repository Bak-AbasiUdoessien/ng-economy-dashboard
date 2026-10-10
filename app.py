"""
app.py  -  Nigeria & Peers Economic Dashboard (Streamlit)
Run locally:   streamlit run app.py
Live version:  deploy free on Streamlit Community Cloud (see README).
"""

import altair as alt                       # chart library that ships with Streamlit
import streamlit as st                     # turns this script into a web app

import analysis                            # our data + logic module (analysis.py)

st.set_page_config(page_title="Nigeria & Peers: Economic Dashboard", page_icon="📈", layout="wide")


@st.cache_data(ttl=6 * 60 * 60)            # remember the data for 6 hours instead of downloading on every click
def get_data():
    return analysis.load_data()


df, is_demo = get_data()

# ---- Header -----------------------------------------------------------------------------
st.title("Nigeria & Peers: Economic Dashboard")
st.caption("World Bank data for Nigeria, Ghana, Kenya, South Africa and Egypt, refreshed weekly by an "
           "[automated ETL pipeline](https://github.com/Bak-AbasiUdoessien/ng-economic-data-pipeline).")
if is_demo:                                                       # never let made-up data look real
    st.warning("Showing **made-up demo data** because the live data could not be loaded.", icon="⚠️")

# ---- Filters (one row, above everything they affect) ------------------------------------
names = df.drop_duplicates("country_code").set_index("country_code")["country"].to_dict()   # NGA -> Nigeria
indicators = df.drop_duplicates("indicator_code").set_index("indicator_code")["indicator"].to_dict()
col1, col2, col3 = st.columns([2, 2, 3])                          # three side-by-side columns, widths 2:2:3
with col1:
    indicator = st.selectbox("Indicator", list(indicators), format_func=indicators.get,   # show names, return codes
                             index=list(indicators).index("FP.CPI.TOTL.ZG") if "FP.CPI.TOTL.ZG" in indicators else 0)
with col2:
    countries = st.multiselect("Countries", list(names), default=list(names), format_func=names.get)
with col3:
    lo, hi = int(df["year"].min()), int(df["year"].max())
    years = st.slider("Years", lo, hi, (max(lo, hi - 15), hi))   # default: the last 15 years

if not countries:
    st.info("Pick at least one country.")
    st.stop()                                                     # end the script here for this run

view = analysis.filter_data(df, countries, years)

# ---- KPI tiles: Nigeria's latest numbers ------------------------------------------------
st.subheader("Nigeria at a glance")
tiles = st.columns(4)
for tile, code in zip(tiles, ["FP.CPI.TOTL.ZG", "NY.GDP.MKTP.KD.ZG", "PA.NUS.FCRF", "SL.UEM.TOTL.ZS"]):
    result = analysis.latest_with_delta(df, "NGA", code)
    with tile:
        if result is None or code not in indicators:
            st.metric(indicators.get(code, code), "no data")
            continue
        year, value, change = result
        st.metric(
            label=f"{indicators[code]} ({year})",
            value=f"{value:,.1f}",
            delta=None if change is None else f"{change:+,.1f} vs previous year",
            delta_color="inverse" if code in analysis.HIGHER_IS_WORSE else "normal",  # red when a rise is bad
            help=df.loc[df["indicator_code"] == code, "unit"].iloc[0],   # hover "?" shows the unit
        )

# ---- Main chart: trend over time ---------------------------------------------------------
series = view[view["indicator_code"] == indicator]
unit = series["unit"].iloc[0] if not series.empty else ""
y_title = unit
if indicator in analysis.INDEX_ONLY and not series.empty:        # different currencies -> compare as an index
    series = analysis.index_to_first_year(series)
    y_title = f"Index, first year shown = 100 (raw unit: {unit})"
    st.caption("Exchange rates are in each country's own currency, so they are shown as an index: "
               "100 = the first year shown, 200 = the currency needs twice as many units per US$.")

st.subheader(f"{indicators[indicator]} over time")
if series.empty:
    st.info("No data for this selection.")
else:
    colour = alt.Scale(domain=list(analysis.COUNTRY_COLOURS), range=list(analysis.COUNTRY_COLOURS.values()))
    base = alt.Chart(series).encode(
        x=alt.X("year:O", title=None),                             # :O = ordinal (years as labels)
        y=alt.Y("value:Q", title=y_title),                          # :Q = quantitative (numbers)
        color=alt.Color("country_code:N", scale=colour, title="Country",
                        legend=alt.Legend(orient="top",                # show "Nigeria", not "NGA", in the legend
                                          labelExpr=f"{names}[datum.label]")),
    )
    lines = base.mark_line(strokeWidth=2)
    points = base.mark_point(size=60, filled=True, opacity=0).encode(   # invisible bigger hit-targets for hovering
        tooltip=[alt.Tooltip("country:N", title="Country"), alt.Tooltip("year:O", title="Year"),
                 alt.Tooltip("value:Q", title=indicators[indicator], format=",.2f")])
    last_points = series.sort_values("year").groupby("country_code").tail(1)   # label each line at its end
    labels = alt.Chart(last_points).mark_text(align="left", dx=6, fontSize=12).encode(
        x="year:O", y="value:Q", text="country:N",
        color=alt.value("#52514e"))                                 # labels in neutral text colour, not series colour
    st.altair_chart((lines + points + labels).properties(height=380), use_container_width=True)

    for sentence in analysis.insights(view, indicator):
        st.markdown(f"- {sentence}")

# ---- Ranking: latest year ----------------------------------------------------------------
if indicator not in analysis.INDEX_ONLY:
    ranking = analysis.latest_ranking(view, indicator)
    if not ranking.empty:
        st.subheader("Latest year, ranked")
        bars = alt.Chart(ranking).mark_bar(cornerRadiusEnd=4, height=22).encode(
            y=alt.Y("country:N", sort=list(ranking["country"]), title=None),   # ranking is already biggest-first
            x=alt.X("value:Q", title=unit),
            color=alt.Color("country_code:N", scale=alt.Scale(domain=list(analysis.COUNTRY_COLOURS),
                                                              range=list(analysis.COUNTRY_COLOURS.values())),
                            legend=None),
            tooltip=["country", "year", alt.Tooltip("value:Q", format=",.2f")])
        values = bars.mark_text(align="left", dx=4, color="#52514e").encode(
            text=alt.Text("value:Q", format=",.1f"), color=alt.value("#52514e"))
        st.altair_chart((bars + values).properties(height=40 * len(ranking) + 20), use_container_width=True)

# ---- Data table + download (also the accessible view of every chart) --------------------
with st.expander("See the data"):
    table = view[view["indicator_code"] == indicator][["country", "year", "value", "unit"]]
    st.dataframe(table.sort_values(["country", "year"]), hide_index=True, use_container_width=True)
    st.download_button("Download CSV", table.to_csv(index=False), file_name=f"{indicator}.csv", mime="text/csv")

st.caption("Source: World Bank Open Data (CC BY 4.0). Built with Python, pandas, Altair and Streamlit.")
