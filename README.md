# Solar Power Plant Performance Analysis

A Python engineering data-analysis project for the Kaggle **Solar Power Generation Data** dataset. It includes data cleaning, timestamp synchronization, engineering calculations, inverter/plant reports, six dashboard visualizations, and transparent low-generation screening. It does **not** use machine-learning prediction.

## 1. Dataset

1. Open [Kaggle's Solar Power Generation Data dataset](https://www.kaggle.com/datasets/anikannal/solar-power-generation-data) and download the dataset archive.
2. Extract the four CSV files below directly into this project's `data/` folder. The dashboard detects a complete local set automatically when it starts.
3. Alternatively, leave `data/` empty and upload the CSV files from the dashboard welcome screen or sidebar. Uploaded files take precedence over local files for that session.

Expected filenames:
- `Plant_1_Generation_Data.csv`
- `Plant_1_Weather_Sensor_Data.csv`
- `Plant_2_Generation_Data.csv`
- `Plant_2_Weather_Sensor_Data.csv`

The data card describes inverter-level generation readings sampled at roughly 15-minute intervals and plant-level weather readings. Generation records contain `DC_POWER`, `AC_POWER`, `DAILY_YIELD`, and `TOTAL_YIELD`; weather records include ambient temperature, module temperature, and irradiation.

## 2. Setup (Windows)

Open Command Prompt in this project folder:

```bat
py -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 3. Run the dashboard

```bat
streamlit run app.py
```

Place all four CSV files in `data/` to load them automatically, or upload them using the welcome screen or sidebar. The dashboard offers date and plant filters, overview charts, inverter comparison, environmental analysis, low-generation review, and CSV/ZIP downloads. The `data/*.csv` rule in `.gitignore` prevents the dataset from being committed.

## 4. Run tests

```bat
pytest -q
```

## 5. Analysis methods

- **Cleaning:** normalizes column names, parses timestamps, removes invalid power values, and deduplicates timestamp/inverter records.
- **Synchronization:** aligns plant-level weather readings to inverter readings by plant and nearest timestamp, with an 8-minute tolerance.
- **Plant power:** sums inverter AC/DC power at each timestamp.
- **Estimated energy:** integrates sampled power over the actual time to the next sample. Gaps over one hour and the last reading in each time series are excluded because the following interval is unknown.
- **Inverter report:** estimates AC energy and summarizes mean/peak power, irradiation, module temperature, and mean AC/DC ratio.
- **Low-generation screening:** during daylight-like conditions (`IRRADIATION >= 0.2`), flags plant-time observations below that plant's 10th-percentile AC power for the same hour. This is a review queue, not a diagnosis.
- **Correlation:** calculates Pearson correlations for irradiation vs AC power, module temperature vs AC power, and ambient vs module temperature.

## 6. Important engineering limitations

1. The dataset does not provide a verified installed capacity for every inverter in the CSV, so capacity-normalized performance ratio is not calculated.
2. AC/DC ratio is a proxy based on synchronized power samples. It can be distorted by timing mismatch, low-power readings, curtailment, clipping, sensor noise, or missing measurements. It is not automatically a certified inverter efficiency.
3. The weather sensors are plant-level measurements; they may not describe every inverter's local conditions.
4. The sampled power readings are instantaneous snapshots. Energy is estimated by integrating power over the elapsed time to the next observation. Compare estimates with `DAILY_YIELD`/`TOTAL_YIELD` only after checking the source units and semantics.
5. An unusual drop does not prove equipment failure. Review irradiation, temperature, timestamps, and inverter-level data before drawing conclusions.
6. No actual findings are stated in advance. The dashboard reports results from the CSVs that you upload.

## 7. Project structure

```text
solar_power_plant_analysis/
├── app.py
├── requirements.txt
├── README.md
├── src/
│   └── solar_analysis.py
├── tests/
│   └── test_analysis.py
├── data/       # place local copies here if desired
└── outputs/    # optional location for exported reports
```

## 8. Suggested report sections for submission

1. Problem statement and objectives
2. Dataset description and columns
3. Data cleaning and timestamp synchronization
4. Engineering formulas and assumptions
5. Daily/hourly generation analysis
6. Inverter-wise comparison
7. Irradiation and temperature relationships
8. Low-generation intervals and possible causes
9. Dashboard screenshots
10. Limitations and conclusion

**Dataset source:** Ani Kannal, *Solar Power Generation Data*, Kaggle. Cite the dataset page in your submission and follow its stated data license/terms.
