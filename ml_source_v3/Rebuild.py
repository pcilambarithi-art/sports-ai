import pandas as pd
import numpy as np
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_FILE = "workout_dataset_70000_rows.xlsx"
OUTPUT_FILE = "workout_dataset_70000_rebuilt.xlsx"

RANDOM_SEED = 42


# ============================================================
# LOAD DATASET
# ============================================================

print("=" * 70)
print("LOADING DATASET")
print("=" * 70)

df = pd.read_excel(INPUT_FILE)

print(f"Rows loaded: {len(df):,}")


# ============================================================
# RANDOM GENERATOR
# ============================================================

rng = np.random.default_rng(RANDOM_SEED)


# ============================================================
# EXERCISE INTENSITY
# ============================================================

exercise_intensity = {
    "Walking": 0.80,
    "Yoga": 0.65,
    "Weight Training": 0.95,
    "Cycling": 1.05,
    "Rowing": 1.15,
    "Swimming": 1.20,
    "Running": 1.30,
    "HIIT": 1.45
}

df["Exercise_Intensity"] = (
    df["Exercise_Type"]
    .map(exercise_intensity)
    .fillna(1.0)
)


# ============================================================
# HEART RATE FACTOR
# ============================================================

heart_rate_factor = (
    0.70 +
    0.006 * (df["Heart_Rate_BPM"] - 100)
)

heart_rate_factor = heart_rate_factor.clip(
    0.65,
    1.55
)


# ============================================================
# AGE FACTOR
# ============================================================

age_factor = (
    1.10 -
    0.004 * (df["Age"] - 20)
)

age_factor = age_factor.clip(
    0.75,
    1.10
)


# ============================================================
# WEIGHT FACTOR
# ============================================================

weight_factor = (
    df["Weight_KG"] / 70.0
).clip(
    0.60,
    1.70
)


# ============================================================
# GENDER FACTOR
# ============================================================

gender_factor = np.where(
    df["Gender"].astype(str).str.lower() == "male",
    1.04,
    0.98
)


# ============================================================
# EXPERIENCE FACTOR
# ============================================================

experience_factor = (
    df["Experience_Level"]
    .map({
        "Beginner": 0.96,
        "Intermediate": 1.00,
        "Advanced": 1.04
    })
    .fillna(1.0)
)


# ============================================================
# CALCULATE CALORIES
# ============================================================

base_calories = (
    df["Duration_Minutes"]
    * 6.0
    * df["Exercise_Intensity"]
    * heart_rate_factor
    * age_factor
    * weight_factor
    * gender_factor
    * experience_factor
)


# ============================================================
# ADD REALISTIC NOISE
# ============================================================

noise = rng.normal(
    loc=0,
    scale=np.maximum(
        base_calories * 0.15,
        8
    )
)

calories = base_calories + noise


# ============================================================
# LIMIT CALORIE RANGE
# ============================================================

df["Calories_Burned"] = np.clip(
    np.round(calories),
    80,
    1500
).astype(int)


# ============================================================
# REMOVE TEMPORARY COLUMN
# ============================================================

df.drop(
    columns=["Exercise_Intensity"],
    inplace=True
)


# ============================================================
# SAVE NEW DATASET
# ============================================================

df.to_excel(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# CHECK RESULTS
# ============================================================

print("\n" + "=" * 70)
print("DATASET REBUILT")
print("=" * 70)

print(f"\nRows          : {len(df):,}")
print(f"Output file   : {OUTPUT_FILE}")

print("\nCalories statistics:")
print(
    df["Calories_Burned"].describe()
)


# ============================================================
# CORRELATION CHECK
# ============================================================

print("\n" + "=" * 70)
print("CORRELATION WITH CALORIES")
print("=" * 70)

numeric_columns = [
    "Age",
    "Duration_Minutes",
    "Heart_Rate_BPM",
    "Workout_Frequency_Per_Week",
    "Sleep_Hours",
    "Water_Intake_Liters",
    "Weight_KG",
    "Calories_Burned"
]

print(
    df[numeric_columns]
    .corr()["Calories_Burned"]
    .sort_values(ascending=False)
)


# ============================================================
# SAMPLE
# ============================================================

print("\n" + "=" * 70)
print("SAMPLE DATA")
print("=" * 70)

print(
    df.head(10).to_string(index=False)
)

print("\nDone!")