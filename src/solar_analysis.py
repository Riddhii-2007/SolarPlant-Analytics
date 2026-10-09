"""Data preparation and engineering analysis for the Solar Power Plant project."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional, Tuple
import numpy as np
import pandas as pd

GENERATION_REQUIRED = {"DATE_TIME", "PLANT_ID", "SOURCE_KEY", "DC_POWER", "AC_POWER"}
WEATHER_REQUIRED = {"DATE_TIME", "PLANT_ID", "AMBIENT_TEMPERATURE", "MODULE_TEMPERATURE", "IRRADIATION"}


def read_csv_safely(source) -> pd.DataFrame:
    """Read a CSV path or file-like object and normalize column names."""
    df = pd.read_csv(source)
    df.columns = [str(c).strip().upper() for c in df.columns]
    return df


def clean_generation(df: pd.DataFrame, plant_label: Optional[str] = None) -> pd.DataFrame:
    """Clean inverter-level generation data without fabricating measurements."""
    out = df.copy()
    out.columns = [str(c).strip().upper() for c in out.columns]
    missing = GENERATION_REQUIRED - set(out.columns)
    if missing:
        raise ValueError(f"Generation file is missing required columns: {sorted(missing)}")
    out["DATE_TIME"] = pd.to_datetime(out["DATE_TIME"], errors="coerce", dayfirst=False)
    out = out.dropna(subset=["DATE_TIME", "SOURCE_KEY"])
    for col in ["DC_POWER", "AC_POWER", "DAILY_YIELD", "TOTAL_YIELD"]:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    out = out.dropna(subset=["DC_POWER", "AC_POWER"])
    out = out[(out["DC_POWER"] >= 0) & (out["AC_POWER"] >= 0)]
    out["PLANT_ID"] = out["PLANT_ID"].astype(str)
    out["SOURCE_KEY"] = out["SOURCE_KEY"].astype(str)
    if plant_label:
        out["PLANT_NAME"] = plant_label
    else:
        out["PLANT_NAME"] = "Plant " + out["PLANT_ID"]
    out = out.drop_duplicates(subset=["DATE_TIME", "PLANT_ID", "SOURCE_KEY"], keep="last")
    return out.sort_values(["PLANT_NAME", "SOURCE_KEY", "DATE_TIME"]).reset_index(drop=True)


def clean_weather(df: pd.DataFrame, plant_label: Optional[str] = None) -> pd.DataFrame:
    """Clean plant-level weather sensor readings."""
    out = df.copy()
    out.columns = [str(c).strip().upper() for c in out.columns]
    missing = WEATHER_REQUIRED - set(out.columns)
    if missing:
        raise ValueError(f"Weather file is missing required columns: {sorted(missing)}")
    out["DATE_TIME"] = pd.to_datetime(out["DATE_TIME"], errors="coerce", dayfirst=False)
    for col in ["AMBIENT_TEMPERATURE", "MODULE_TEMPERATURE", "IRRADIATION"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out = out.dropna(subset=["DATE_TIME"])
    out["PLANT_ID"] = out["PLANT_ID"].astype(str)
    out = out.drop_duplicates(subset=["DATE_TIME", "PLANT_ID"], keep="last")
    if plant_label:
        out["PLANT_NAME"] = plant_label
    else:
        out["PLANT_NAME"] = "Plant " + out["PLANT_ID"]
    return out.sort_values(["PLANT_NAME", "DATE_TIME"]).reset_index(drop=True)


def combine_uploaded_files(files: Dict[str, object]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load the four Kaggle CSVs from a mapping of filename -> path/file-like."""
    gen_frames, weather_frames = [], []
    for filename, source in files.items():
        name = filename.lower()
        if "generation" in name:
            gen_frames.append(clean_generation(read_csv_safely(source)))
        elif "weather" in name or "sensor" in name:
            weather_frames.append(clean_weather(read_csv_safely(source)))
    if not gen_frames:
        raise ValueError("Upload at least one generation CSV file.")
    if not weather_frames:
        raise ValueError("Upload at least one weather/sensor CSV file.")
    generation = pd.concat(gen_frames, ignore_index=True)
    weather = pd.concat(weather_frames, ignore_index=True)
    # Keep plant identifiers consistent between the generation and weather files.
    generation["PLANT_ID"] = generation["PLANT_ID"].astype(str)
    weather["PLANT_ID"] = weather["PLANT_ID"].astype(str)
    return generation, weather


def merge_weather(generation: pd.DataFrame, weather: pd.DataFrame) -> pd.DataFrame:
    """Synchronize inverter observations with plant-level weather by nearest timestamp."""
    left = generation.copy()
    right = weather.copy()
    left["DATE_TIME"] = pd.to_datetime(left["DATE_TIME"], errors="coerce")
    right["DATE_TIME"] = pd.to_datetime(right["DATE_TIME"], errors="coerce")
    # Merge on plant and nearest timestamp. The source data is normally 15-minute sampled.
    merged = pd.merge_asof(
        left.sort_values("DATE_TIME"),
        right.sort_values("DATE_TIME"),
        on="DATE_TIME",
        by="PLANT_ID",
        direction="nearest",
        tolerance=pd.Timedelta("8min"),
        suffixes=("", "_WEATHER"),
    )
    # Resolve duplicated plant label from merge suffixes.
    if "PLANT_NAME_WEATHER" in merged.columns:
        merged["PLANT_NAME"] = merged["PLANT_NAME"].fillna(merged["PLANT_NAME_WEATHER"])
        merged = merged.drop(columns=["PLANT_NAME_WEATHER"])
    return merged.sort_values(["PLANT_NAME", "SOURCE_KEY", "DATE_TIME"]).reset_index(drop=True)


def build_timeseries(generation: pd.DataFrame, weather: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Return synchronized inverter-level rows and plant-time aggregated rows."""
    inv = merge_weather(generation, weather)
    inv["DATE"] = inv["DATE_TIME"].dt.date.astype(str)
    inv["HOUR"] = inv["DATE_TIME"].dt.hour
    # Summing inverter AC/DC at a timestamp gives plant power at that timestamp.
    group_cols = ["PLANT_NAME", "PLANT_ID", "DATE_TIME", "DATE", "HOUR"]
    aggregations = {"DC_POWER": "sum", "AC_POWER": "sum"}
    for col in ["AMBIENT_TEMPERATURE", "MODULE_TEMPERATURE", "IRRADIATION"]:
        if col in inv.columns:
            aggregations[col] = "mean"
    plant_ts = inv.groupby(group_cols, as_index=False).agg(aggregations)
    plant_ts["AC_DC_EFFICIENCY_PCT"] = np.where(
        plant_ts["DC_POWER"] > 0,
        plant_ts["AC_POWER"] / plant_ts["DC_POWER"] * 100,
        np.nan,
    )
    return inv, plant_ts


def estimate_energy_kwh(df: pd.DataFrame, group_cols, power_col: str = "AC_POWER") -> pd.DataFrame:
    """Estimate energy from sampled power using elapsed time to the next reading.

    Each inverter/plant time series uses its own actual interval. The final sample
    has no known following interval and is excluded rather than assumed.
    """
    work = df.sort_values(list(group_cols) + ["DATE_TIME"]).copy()
    work["_NEXT_TIME"] = work.groupby(list(group_cols))["DATE_TIME"].shift(-1)
    work["_HOURS"] = (work["_NEXT_TIME"] - work["DATE_TIME"]).dt.total_seconds() / 3600
    # Reject implausible gaps; expected sampling interval is about 15 minutes.
    work.loc[(work["_HOURS"] <= 0) | (work["_HOURS"] > 1), "_HOURS"] = np.nan
    work["_ENERGY_KWH"] = work[power_col] * work["_HOURS"]
    return work


def daily_generation(plant_ts: pd.DataFrame) -> pd.DataFrame:
    work = estimate_energy_kwh(plant_ts, ["PLANT_NAME"], "AC_POWER")
    daily = work.groupby(["PLANT_NAME", "DATE"], as_index=False).agg(
        ENERGY_KWH=("_ENERGY_KWH", "sum"),
        MEAN_AC_POWER_KW=("AC_POWER", "mean"),
        PEAK_AC_POWER_KW=("AC_POWER", "max"),
        MEAN_IRRADIATION=("IRRADIATION", "mean"),
        MEAN_MODULE_TEMP_C=("MODULE_TEMPERATURE", "mean"),
    )
    return daily


def hourly_generation(plant_ts: pd.DataFrame) -> pd.DataFrame:
    work = estimate_energy_kwh(plant_ts, ["PLANT_NAME"], "AC_POWER")
    work["HOUR_LABEL"] = work["DATE_TIME"].dt.hour
    return work.groupby(["PLANT_NAME", "HOUR_LABEL"], as_index=False).agg(
        ESTIMATED_ENERGY_KWH=("_ENERGY_KWH", "sum"),
        MEAN_AC_POWER_KW=("AC_POWER", "mean"),
        PEAK_AC_POWER_KW=("AC_POWER", "max"),
    )


def inverter_report(inverter_ts: pd.DataFrame) -> pd.DataFrame:
    work = estimate_energy_kwh(inverter_ts, ["PLANT_NAME", "SOURCE_KEY"], "AC_POWER")
    report = work.groupby(["PLANT_NAME", "SOURCE_KEY"], as_index=False).agg(
        ESTIMATED_AC_ENERGY_KWH=("_ENERGY_KWH", "sum"),
        MEAN_AC_POWER_KW=("AC_POWER", "mean"),
        PEAK_AC_POWER_KW=("AC_POWER", "max"),
        MEAN_DC_POWER_KW=("DC_POWER", "mean"),
        MEAN_IRRADIATION=("IRRADIATION", "mean"),
        MEAN_MODULE_TEMP_C=("MODULE_TEMPERATURE", "mean"),
    )
    report["MEAN_CONVERSION_EFFICIENCY_PCT"] = np.where(
        report["MEAN_DC_POWER_KW"] > 0,
        report["MEAN_AC_POWER_KW"] / report["MEAN_DC_POWER_KW"] * 100,
        np.nan,
    )
    return report.sort_values(["PLANT_NAME", "ESTIMATED_AC_ENERGY_KWH"], ascending=[True, False])


def find_low_generation_periods(plant_ts: pd.DataFrame, irradiation_threshold: float = 0.2) -> pd.DataFrame:
    """Flag low-output daylight periods using per-plant, per-hour 10th percentile.

    This is a transparent screening rule, not a fault diagnosis. Irradiance is
    expected to be in the dataset's usual kW/m²-like scale.
    """
    df = plant_ts.copy()
    if "IRRADIATION" not in df.columns:
        return pd.DataFrame(columns=list(df.columns) + ["LOW_GENERATION_FLAG", "HOURLY_P10_KW"])
    daylight = df[df["IRRADIATION"].fillna(0) >= irradiation_threshold].copy()
    if daylight.empty:
        daylight["HOURLY_P10_KW"] = np.nan
        daylight["LOW_GENERATION_FLAG"] = False
        return daylight
    daylight["HOUR"] = daylight["DATE_TIME"].dt.hour
    thresholds = daylight.groupby(["PLANT_NAME", "HOUR"])["AC_POWER"].quantile(0.10).rename("HOURLY_P10_KW")
    daylight = daylight.join(thresholds, on=["PLANT_NAME", "HOUR"])
    daylight["LOW_GENERATION_FLAG"] = daylight["AC_POWER"] < daylight["HOURLY_P10_KW"]
    return daylight[daylight["LOW_GENERATION_FLAG"]].sort_values("DATE_TIME")


def correlation_report(plant_ts: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for plant, group in plant_ts.groupby("PLANT_NAME"):
        rows.append({
            "PLANT_NAME": plant,
            "IRRADIATION_AC_POWER_CORRELATION": group["IRRADIATION"].corr(group["AC_POWER"]),
            "MODULE_TEMP_AC_POWER_CORRELATION": group["MODULE_TEMPERATURE"].corr(group["AC_POWER"]),
            "AMBIENT_TEMP_MODULE_TEMP_CORRELATION": group["AMBIENT_TEMPERATURE"].corr(group["MODULE_TEMPERATURE"]),
        })
    return pd.DataFrame(rows)


def make_reports(generation: pd.DataFrame, weather: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    inverter_ts, plant_ts = build_timeseries(generation, weather)
    return {
        "synchronized_inverter_data": inverter_ts,
        "plant_timeseries": plant_ts,
        "daily_generation": daily_generation(plant_ts),
        "hourly_generation": hourly_generation(plant_ts),
        "inverter_report": inverter_report(inverter_ts),
        "low_generation_periods": find_low_generation_periods(plant_ts),
        "correlation_report": correlation_report(plant_ts),
    }
