from pathlib import Path
import io
import zipfile
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

from src.solar_analysis import combine_uploaded_files, find_local_dataset, make_reports

DATA_DIR = Path(__file__).resolve().parent / "data"
local_files = find_local_dataset(DATA_DIR)

st.set_page_config(page_title="Solar Plant Performance", page_icon="☀️", layout="wide")
st.markdown("""
<style>
.block-container {padding-top: 1.5rem; max-width: 1500px;}
[data-testid="stMetric"] {background: #f6f3eb; border: 1px solid #e6dfcf; padding: 14px; border-radius: 12px;}
/* Keep metric text readable when Streamlit's dark theme supplies light text. */
[data-testid="stMetric"] [data-testid="stMetricLabel"],
[data-testid="stMetric"] [data-testid="stMetricValue"],
[data-testid="stMetric"] [data-testid="stMetricDelta"] {
    color: #1f2937 !important;
}
</style>
""", unsafe_allow_html=True)

st.title("☀️ Solar Plant Performance Analysis")
st.caption("Engineering data analysis dashboard · Pandas, NumPy, statistical screening · No ML prediction")

welcome_uploaded = []
if not local_files:
    with st.container(border=True):
        st.subheader("Explore your solar plant data")
        st.write("Analyze inverter output, environmental conditions, estimated energy, and low-generation intervals from the Kaggle Solar Power Generation Data dataset.")
        welcome_uploaded = st.file_uploader(
            "Upload your dataset CSV files",
            type=["csv"],
            accept_multiple_files=True,
            key="welcome_upload",
            help="Select the four Kaggle CSV files to populate the dashboard.",
        )
        st.caption("Required: Plant_1 and Plant_2 generation CSVs plus their weather sensor CSVs.")

with st.sidebar:
    st.header("Data")
    st.write("A complete dataset in `data/` loads automatically. Upload CSV files here to analyze a different dataset.")
    sidebar_uploaded = st.file_uploader(
        "Select CSV files",
        type=["csv"],
        accept_multiple_files=True,
        key="sidebar_upload",
        help="Include filenames containing 'Generation' and 'Weather' or 'Sensor'.",
    )
    st.markdown("[Open the Kaggle dataset](https://www.kaggle.com/datasets/anikannal/solar-power-generation-data)")
    st.divider()
    st.subheader("Analysis notes")
    st.caption("The dashboard estimates energy by integrating sampled AC power over actual time intervals. The final sample in each series is excluded because its next interval is unknown.")
    st.caption("Low-generation flags are screening signals, not confirmed faults.")

uploaded = sidebar_uploaded or welcome_uploaded
if uploaded:
    file_map = {file.name: file for file in uploaded}
    data_source = "uploaded files"
elif local_files:
    file_map = local_files
    data_source = "local data/ folder"
else:
    st.info("Upload the four required CSV files above to begin.")
    st.stop()

try:
    generation, weather = combine_uploaded_files(file_map)
    reports = make_reports(generation, weather)
except Exception as exc:
    st.error(f"Could not process the {data_source}: {exc}")
    st.stop()

st.caption(f"Data source: {data_source}")

plant_ts = reports["plant_timeseries"]
daily = reports["daily_generation"]
hourly = reports["hourly_generation"]
inverters = reports["inverter_report"]
low = reports["low_generation_periods"]
corr = reports["correlation_report"]

if plant_ts.empty:
    st.warning("No synchronized records are available. Check the timestamp formats and matching plant IDs.")
    st.stop()

with st.sidebar:
    plants = sorted(plant_ts["PLANT_NAME"].dropna().unique().tolist())
    chosen_plants = st.multiselect("Plants", plants, default=plants)
    min_date = pd.to_datetime(plant_ts["DATE"]).min().date()
    max_date = pd.to_datetime(plant_ts["DATE"]).max().date()
    date_range = st.date_input("Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)

if len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = end_date = date_range[0]

filtered = plant_ts[
    plant_ts["PLANT_NAME"].isin(chosen_plants)
    & (pd.to_datetime(plant_ts["DATE"]).dt.date >= start_date)
    & (pd.to_datetime(plant_ts["DATE"]).dt.date <= end_date)
].copy()
filtered_daily = daily[
    daily["PLANT_NAME"].isin(chosen_plants)
    & (pd.to_datetime(daily["DATE"]).dt.date >= start_date)
    & (pd.to_datetime(daily["DATE"]).dt.date <= end_date)
].copy()
filtered_hourly = hourly[hourly["PLANT_NAME"].isin(chosen_plants)].copy()
filtered_inverters = inverters[inverters["PLANT_NAME"].isin(chosen_plants)].copy()
filtered_low = low[
    low["PLANT_NAME"].isin(chosen_plants)
    & (pd.to_datetime(low["DATE"]).dt.date >= start_date)
    & (pd.to_datetime(low["DATE"]).dt.date <= end_date)
].copy()

total_energy = filtered_daily["ENERGY_KWH"].sum()
peak_power = filtered["AC_POWER"].max() if not filtered.empty else 0
mean_eff = filtered.loc[filtered["DC_POWER"] > 0, "AC_DC_EFFICIENCY_PCT"].replace([float("inf"), -float("inf")], pd.NA).dropna().median()
flag_count = len(filtered_low)

st.subheader("Plant overview")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Estimated AC energy", f"{total_energy:,.1f} kWh")
c2.metric("Peak observed AC power", f"{peak_power:,.2f} kW")
c3.metric("Median AC/DC ratio", "—" if pd.isna(mean_eff) else f"{mean_eff:,.1f}%")
c4.metric("Low-generation flags", f"{flag_count:,}")

tab_overview, tab_inverter, tab_environment, tab_flags, tab_data = st.tabs(
    ["Generation overview", "Inverter performance", "Environment", "Low-generation review", "Data & downloads"]
)

sns.set_theme(style="whitegrid")
with tab_overview:
    left, right = st.columns(2)
    with left:
        st.markdown("#### Daily energy generation")
        if not filtered_daily.empty:
            fig, ax = plt.subplots(figsize=(9, 4))
            for plant, group in filtered_daily.groupby("PLANT_NAME"):
                ax.plot(pd.to_datetime(group["DATE"]), group["ENERGY_KWH"], marker="o", linewidth=1.8, label=plant)
            ax.set_xlabel("Date")
            ax.set_ylabel("Estimated AC energy (kWh)")
            ax.legend()
            fig.autofmt_xdate()
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)
    with right:
        st.markdown("#### Hourly generation profile")
        if not filtered_hourly.empty:
            fig, ax = plt.subplots(figsize=(9, 4))
            for plant, group in filtered_hourly.groupby("PLANT_NAME"):
                ax.plot(group["HOUR_LABEL"], group["ESTIMATED_ENERGY_KWH"], marker="o", label=plant)
            ax.set_xlabel("Hour of day")
            ax.set_ylabel("Estimated AC energy (kWh)")
            ax.set_xticks(range(0, 24, 2))
            ax.legend()
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)
    st.markdown("#### Plant generation heatmap")
    if not filtered.empty:
        heat = filtered.pivot_table(index="DATE", columns="HOUR", values="AC_POWER", aggfunc="mean")
        fig, ax = plt.subplots(figsize=(12, max(3, min(8, len(heat) * 0.25))))
        sns.heatmap(heat, cmap="YlOrBr", ax=ax, cbar_kws={"label": "Mean AC power (kW)"})
        ax.set_xlabel("Hour of day")
        ax.set_ylabel("Date")
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)

with tab_inverter:
    st.markdown("#### Inverter energy and output")
    if not filtered_inverters.empty:
        fig, ax = plt.subplots(figsize=(11, 5))
        plot_data = filtered_inverters.sort_values("ESTIMATED_AC_ENERGY_KWH", ascending=False)
        sns.barplot(data=plot_data, x="SOURCE_KEY", y="ESTIMATED_AC_ENERGY_KWH", hue="PLANT_NAME", ax=ax)
        ax.set_xlabel("Inverter / source key")
        ax.set_ylabel("Estimated AC energy (kWh)")
        ax.tick_params(axis="x", rotation=70)
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
        st.dataframe(filtered_inverters, use_container_width=True, hide_index=True)
    st.markdown("#### AC vs DC power")
    if not filtered.empty:
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.scatterplot(data=filtered.sample(min(len(filtered), 6000), random_state=42), x="DC_POWER", y="AC_POWER", hue="PLANT_NAME", alpha=0.45, ax=ax)
        ax.set_xlabel("DC power (kW)")
        ax.set_ylabel("AC power (kW)")
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)

with tab_environment:
    left, right = st.columns(2)
    with left:
        st.markdown("#### Irradiation vs AC power")
        plot = filtered.dropna(subset=["IRRADIATION", "AC_POWER"])
        if not plot.empty:
            fig, ax = plt.subplots(figsize=(7, 4))
            sns.scatterplot(data=plot.sample(min(len(plot), 6000), random_state=42), x="IRRADIATION", y="AC_POWER", hue="PLANT_NAME", alpha=0.4, ax=ax)
            ax.set_xlabel("Irradiation (dataset units)")
            ax.set_ylabel("AC power (kW)")
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)
    with right:
        st.markdown("#### Module and ambient temperature")
        temp = filtered.dropna(subset=["MODULE_TEMPERATURE", "AMBIENT_TEMPERATURE"])
        if not temp.empty:
            by_hour = temp.groupby("HOUR", as_index=False)[["MODULE_TEMPERATURE", "AMBIENT_TEMPERATURE"]].mean()
            fig, ax = plt.subplots(figsize=(7, 4))
            ax.plot(by_hour["HOUR"], by_hour["MODULE_TEMPERATURE"], marker="o", label="Module")
            ax.plot(by_hour["HOUR"], by_hour["AMBIENT_TEMPERATURE"], marker="o", label="Ambient")
            ax.set_xlabel("Hour of day")
            ax.set_ylabel("Temperature (°C)")
            ax.legend()
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)
    st.markdown("#### Correlation summary")
    st.dataframe(corr[corr["PLANT_NAME"].isin(chosen_plants)], use_container_width=True, hide_index=True)
    st.caption("Pearson correlation describes linear association; it does not establish causation.")

with tab_flags:
    st.markdown("#### Low-generation intervals for investigation")
    st.write("Rule: irradiation at or above 0.2 and AC power below the 10th percentile for that plant and hour. This is a screening rule, not a confirmed equipment fault.")
    st.dataframe(filtered_low, use_container_width=True, hide_index=True)
    if filtered_low.empty:
        st.success("No intervals met the current screening rule in the selected filters.")

with tab_data:
    st.markdown("#### Cleaned and calculated tables")
    chosen_table = st.selectbox("Choose report", list(reports.keys()))
    st.dataframe(reports[chosen_table], use_container_width=True, hide_index=True)
    csv_bytes = reports[chosen_table].to_csv(index=False).encode("utf-8")
    st.download_button("Download selected report as CSV", data=csv_bytes, file_name=f"{chosen_table}.csv", mime="text/csv")
    # Bundle all processed reports for convenient submission.
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, table in reports.items():
            zf.writestr(f"{name}.csv", table.to_csv(index=False))
    st.download_button("Download all processed reports (ZIP)", data=buffer.getvalue(), file_name="solar_analysis_reports.zip", mime="application/zip")

st.divider()
st.caption("Engineering caution: AC/DC ratio can exceed 100% in noisy or misaligned records. Investigate timestamp synchronization, sensor quality, clipping, and units before interpreting any metric as physical efficiency.")
