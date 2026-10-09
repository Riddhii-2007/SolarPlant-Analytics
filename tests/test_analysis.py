import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import numpy as np
from src.solar_analysis import clean_generation, clean_weather, build_timeseries, daily_generation, estimate_energy_kwh, find_local_dataset, find_low_generation_periods


def sample_frames():
    times = pd.date_range("2025-01-01 06:00", periods=5, freq="15min")
    generation = pd.DataFrame({
        "DATE_TIME": list(times) * 2,
        "PLANT_ID": ["1"] * 10,
        "SOURCE_KEY": ["INV_A"] * 5 + ["INV_B"] * 5,
        "DC_POWER": [0, 10, 20, 30, 20] * 2,
        "AC_POWER": [0, 9, 18, 27, 18] * 2,
    })
    weather = pd.DataFrame({
        "DATE_TIME": times,
        "PLANT_ID": ["1"] * 5,
        "AMBIENT_TEMPERATURE": [20, 21, 22, 23, 22],
        "MODULE_TEMPERATURE": [21, 25, 30, 35, 30],
        "IRRADIATION": [0.0, 0.3, 0.5, 0.7, 0.4],
    })
    return generation, weather


def test_clean_generation_deduplicates_and_parses():
    gen, _ = sample_frames()
    gen = pd.concat([gen, gen.iloc[[0]]], ignore_index=True)
    cleaned = clean_generation(gen)
    assert len(cleaned) == 10
    assert pd.api.types.is_datetime64_any_dtype(cleaned["DATE_TIME"])


def test_find_local_dataset_requires_all_four_expected_files(tmp_path):
    expected = [
        "Plant_1_Generation_Data.csv",
        "Plant_1_Weather_Sensor_Data.csv",
        "Plant_2_Generation_Data.csv",
        "Plant_2_Weather_Sensor_Data.csv",
    ]
    for name in expected[:3]:
        (tmp_path / name).touch()
    assert find_local_dataset(tmp_path) == {}

    (tmp_path / expected[3]).touch()
    found = find_local_dataset(tmp_path)
    assert set(found) == set(expected)
    assert all(path.is_file() for path in found.values())


def test_build_timeseries_and_daily_energy():
    gen, weather = sample_frames()
    g = clean_generation(gen)
    w = clean_weather(weather)
    inv, plant = build_timeseries(g, w)
    assert len(plant) == 5
    assert plant["AC_POWER"].iloc[2] == 36
    daily = daily_generation(plant)
    assert len(daily) == 1
    # Plant power is summed across two inverters, then integrated over four
    # known 15-minute intervals: (0 + 18 + 36 + 54) kW * 0.25 h = 27 kWh.
    assert daily["ENERGY_KWH"].iloc[0] == 27
    # AC and DC are both kW, so the plant-level ratio is dimensionless.
    assert plant.loc[plant["DC_POWER"] > 0, "AC_DC_EFFICIENCY_PCT"].eq(90).all()


def test_energy_uses_actual_intervals_and_excludes_large_gaps():
    df = pd.DataFrame({
        "PLANT_NAME": ["Plant 1", "Plant 1", "Plant 1"],
        "DATE_TIME": pd.to_datetime(["2025-01-01 06:00", "2025-01-01 06:30", "2025-01-01 08:00"]),
        "AC_POWER": [10.0, 20.0, 30.0],
    })

    estimated = estimate_energy_kwh(df, ["PLANT_NAME"])

    assert estimated["_ENERGY_KWH"].iloc[0] == 5.0
    assert pd.isna(estimated["_ENERGY_KWH"].iloc[1])
    assert pd.isna(estimated["_ENERGY_KWH"].iloc[2])


def test_low_generation_flags_only_daylight_records():
    gen, weather = sample_frames()
    g = clean_generation(gen)
    w = clean_weather(weather)
    _, plant = build_timeseries(g, w)
    flagged = find_low_generation_periods(plant)
    assert "LOW_GENERATION_FLAG" in flagged.columns
    assert (flagged["IRRADIATION"] >= 0.2).all()
