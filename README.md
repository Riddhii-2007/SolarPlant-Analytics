# Solar Power Plant Performance Analysis

A Python-based engineering data-analysis project that analyzes solar power generation, inverter performance, environmental conditions, and potential low-generation periods using real-world solar plant data.

The project uses **Pandas, NumPy, Matplotlib, Seaborn, and Streamlit** to transform raw solar generation and weather data into an interactive dashboard with visualizations, statistical analysis, and downloadable results.

## Live Demo

**Website:** https://riddhii-2007-solarplant-analytics-app-kxuj1u.streamlit.app/

You can explore the dashboard directly in your browser. Upload compatible solar generation and weather datasets to perform the analysis.

## 1. Project Overview

Solar power plants generate large amounts of operational data, including AC power, DC power, daily energy yield, inverter readings, solar irradiation, and temperature measurements.

Analyzing these parameters helps us understand how a plant performs under different environmental conditions and identify periods that may require further investigation.

This project provides an interactive interface for analyzing these parameters without manually processing large CSV files.

### Objectives

- Analyze solar power generation across plants and inverters.
- Understand the relationship between solar irradiation and AC power output.
- Compare inverter performance using available generation data.
- Examine the influence of ambient and module temperatures on power generation.
- Identify potential low-generation periods for engineering review.
- Generate visualizations and downloadable analysis results.

## 2. Features

### Generation Overview
- Analyze AC and DC power generation.
- Explore generation trends over time.
- Compare generation across plants.
- Examine daily yield and estimated energy generation.

### Inverter Performance
- Compare inverter-level generation.
- Analyze AC and DC power relationships.
- Identify differences in inverter output for further investigation.

### Environmental Analysis
- Examine solar irradiation and power generation.
- Analyze ambient and module temperatures.
- Explore correlations between environmental parameters and AC power.

### Low-Generation Review
- Screen for potentially low-generation observations under sufficient solar irradiation.
- Compare observations against plant- and hour-specific generation thresholds.
- Highlight periods that may need further engineering investigation.

### Data and Downloads
- Upload compatible CSV files through the dashboard.
- Inspect and analyze the loaded data.
- Download available analysis results for further use.

## 3. Dataset

This project was developed and tested using the **Solar Power Generation Data** dataset available on Kaggle.

**Example dataset:** https://www.kaggle.com/datasets/anikannal/solar-power-generation-data

The reference dataset contains generation readings from two solar plants and associated weather sensor measurements.

### Example Dataset Files

The following four CSV files belong to the example dataset used during development and testing:

1. `Plant_1_Generation_Data.csv`
2. `Plant_1_Weather_Sensor_Data.csv`
3. `Plant_2_Generation_Data.csv`
4. `Plant_2_Weather_Sensor_Data.csv`

**These are example files, not the only datasets the application can analyze.**

You can use the original Kaggle dataset or provide your own compatible solar generation and weather datasets. Your data does not need to come from exactly two plants or use the same plant names as the example dataset.

The important requirement is that your data contains the information needed by the analysis functions and follows a compatible structure.

### Important: Dataset Files Are Not Included in This Repository

The example CSV files are not included in the GitHub repository.

If you clone this repository, you will need to obtain your own data. You can download the example dataset from Kaggle or use your own compatible datasets.

- **For the live website:** Upload your datasets through the dashboard.
- **For local use:** Place the example files or your compatible datasets in the local `data` directory, or upload them through the dashboard.

The application is designed for compatible solar generation and weather data, not arbitrary CSV files. Datasets with different column names or structures may require column mapping or changes to the analysis code.

### Expected Data Fields

The following columns describe the reference dataset and the information used by the analysis.

**Generation data**

| Column | Description |
|---|---|
| `DATE_TIME` | Date and time of the observation |
| `PLANT_ID` | Identifier of the solar plant |
| `SOURCE_KEY` | Identifier of the inverter or generation source |
| `DC_POWER` | DC power reading |
| `AC_POWER` | AC power reading |
| `DAILY_YIELD` | Energy yield recorded for the day |
| `TOTAL_YIELD` | Cumulative energy yield |

**Weather sensor data**

| Column | Description |
|---|---|
| `DATE_TIME` | Date and time of the observation |
| `PLANT_ID` | Identifier of the solar plant |
| `SOURCE_KEY` | Identifier of the weather sensor |
| `AMBIENT_TEMPERATURE` | Ambient temperature |
| `MODULE_TEMPERATURE` | Solar module temperature |
| `IRRADIATION` | Recorded solar irradiation |

These are the column names used by the reference dataset. Your own datasets may use different names, but their fields must be mapped to the structure expected by the analysis code if they are not already compatible.

## 4. Installation and Setup

### Prerequisites

- Python 3.10 or a compatible Python version
- Git
- A web browser

### Step 1: Clone the Repository

```bash
git clone https://github.com/Riddhii-2007/SolarPlant-Analytics.git
```

### Step 2: Navigate to the Project Directory

```bash
cd SolarPlant-Analytics
```

If the cloned repository contains a nested project directory, navigate into the directory containing `app.py`.

### Step 3: Create a Virtual Environment

On Windows:

```bash
py -m venv .venv
```

### Step 4: Activate the Virtual Environment

On Windows Command Prompt:

```bash
.venv\Scripts\activate
```

On PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### Step 5: Install Dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 6: Run the Application

```bash
python -m streamlit run app.py
```

Alternatively:

```bash
streamlit run app.py
```

Streamlit will display a local URL in your terminal. Open that URL in your browser to access the dashboard.

## 5. How to Use the Application

### Option A: Use the Live Website

1. Open the [SolarPlant Analytics dashboard](https://riddhii-2007-solarplant-analytics-app-kxuj1u.streamlit.app/).
2. Download the example dataset from [Kaggle](https://www.kaggle.com/datasets/anikannal/solar-power-generation-data), or prepare your own compatible solar generation and weather datasets.
3. Upload the corresponding CSV files through the dashboard, following the application's upload requirements.
4. Explore the different sections of the application.
5. Review generation trends, inverter performance, environmental relationships, and potential low-generation observations.
6. Download the available analysis results if needed.

### Option B: Run the Project Locally

1. Clone the repository and install the dependencies.
2. Obtain the example dataset or prepare your own compatible datasets.
3. Create a `data` folder in the project directory if it does not already exist.
4. Place your data files in the `data` folder using the filenames and structure expected by the local-loading logic, or upload the files through the dashboard.
5. Run the application using Streamlit.

Example folder structure when using the reference dataset:

```text
SolarPlant-Analytics/
│
├── app.py
├── requirements.txt
├── README.md
│
├── src/
│   └── solar_analysis.py
│
├── tests/
│   └── test_analysis.py
│
├── data/
│   ├── Plant_1_Generation_Data.csv
│   ├── Plant_1_Weather_Sensor_Data.csv
│   ├── Plant_2_Generation_Data.csv
│   └── Plant_2_Weather_Sensor_Data.csv
│
└── outputs/
```

The four CSV filenames shown above are examples from the reference dataset. If you use different filenames or a different data structure, the local-loading logic or analysis code may need to be adjusted.

Dataset files are excluded from Git, so cloning the repository does not download them automatically.

## 6. Analysis Methodology

The project uses data processing, statistical analysis, and engineering-oriented calculations to explore solar plant performance.

### Data Cleaning and Preparation

- Standardizes column names and processes timestamps.
- Handles invalid values in power readings.
- Removes duplicate inverter observations where applicable.
- Prepares generation and weather data for analysis.

### Generation Analysis

- Aggregates inverter AC and DC power readings by plant and timestamp.
- Examines generation trends over time.
- Estimates energy from power readings and elapsed time between observations.

### Energy Estimation

Estimated energy is calculated using power and the elapsed time between consecutive observations:

\[
E = P \times \Delta t
\]

Where:

- \(E\) is estimated energy in kWh.
- \(P\) is power in kW.
- \(\Delta t\) is the elapsed time in hours.

Intervals exceeding one hour and the final observation without a subsequent timestamp are excluded from this estimation to reduce misleading calculations.

This is an estimate based on the available sampling intervals, not a replacement for the plant's official energy meter readings.

### Environmental Analysis

The project examines relationships between:

- Solar irradiation and AC power.
- Module temperature and AC power.
- Ambient temperature and module temperature.

Pearson correlation is used to measure linear relationships between selected variables. Correlation alone does not establish causation.

### Inverter Analysis

Inverter readings are compared using available AC and DC power measurements.

AC and DC power values can differ because they represent different stages of power conversion. A difference between them does not automatically indicate a fault or abnormal inverter efficiency.

### Low-Generation Screening

The application screens observations for potentially low generation under sufficient solar irradiation.

It uses a plant- and hour-specific generation threshold based on the 10th percentile of relevant observations, with irradiation of at least `0.2` as a screening condition.

These observations are flagged for further investigation; they are not automatically classified as confirmed equipment faults.

## 7. Limitations

- The application requires compatible solar generation and weather datasets containing the information needed by the analysis functions.
- The original example dataset is not included in the repository.
- Results depend on the quality, completeness, and sampling frequency of the supplied data.
- Datasets with incompatible column names or structures may require modifications to the data-loading or analysis code.
- Estimated energy depends on the observed power readings and elapsed time between observations.
- Correlation does not prove causation.
- Low-generation flags indicate observations that may warrant investigation, not confirmed failures.
- AC/DC comparisons are analytical indicators and are not certified inverter-efficiency measurements.
- Installed plant capacity is not provided as a reliable input for this analysis, so a capacity-normalized performance ratio is not calculated.
- This project supports exploratory analysis and engineering review; it does not replace professional plant diagnostics or operational monitoring systems.

## 8. Technologies Used

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| Pandas | Data cleaning and manipulation |
| NumPy | Numerical calculations |
| Matplotlib | Data visualization |
| Seaborn | Statistical visualization |
| Streamlit | Interactive web dashboard |
| Pytest | Automated testing |
| Git and GitHub | Version control and project hosting |

## 9. Running Tests

The project includes automated tests for selected data-analysis functions.

After installing the dependencies, run:

```bash
python -m pytest
```

The tests help verify the behavior of supported analysis functions and data-handling logic.

## 10. Project Structure

```text
SolarPlant-Analytics/
│
├── app.py                    # Streamlit dashboard
├── requirements.txt          # Python dependencies
├── README.md                 # Project documentation
├── .gitignore                # Excluded files
│
├── src/
│   └── solar_analysis.py     # Data processing and analysis logic
│
├── tests/
│   └── test_analysis.py      # Automated tests
│
├── data/
│   └── README.md             # Dataset instructions
│
└── outputs/
    └── .gitkeep              # Keeps the output directory in Git
```

## Conclusion

SolarPlant Analytics demonstrates how Python-based data analysis can be applied to solar power generation data to explore plant performance, inverter readings, environmental relationships, and potential low-generation periods.

By combining data processing, statistical analysis, engineering calculations, and an interactive dashboard, the project provides a practical starting point for understanding operational solar energy data.

The application uses a Kaggle dataset as a reference, but it can also be adapted to work with other compatible solar generation and weather datasets.

## Author

**GitHub:** https://github.com/Riddhii-2007

**Repository:** https://github.com/Riddhii-2007/SolarPlant-Analytics

**Live Application:** https://riddhii-2007-solarplant-analytics-app-kxuj1u.streamlit.app/

## Dataset Attribution

The example dataset used for developing and testing this project is available on Kaggle:

https://www.kaggle.com/datasets/anikannal/solar-power-generation-data

Please refer to the original dataset page for its licensing terms and usage conditions.
