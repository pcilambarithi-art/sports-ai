import pandas as pd
import numpy as np
import joblib
import os

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_FILE = "workout_dataset_70000_rebuilt.xlsx"

OUTPUT_FILE = "preprocessed_workout_dataset.csv"
PREPROCESSOR_FILE = "trained_models/preprocessor.pkl"

os.makedirs("trained_models", exist_ok=True)


# ============================================================
# LOAD DATASET
# ============================================================

print("=" * 70)
print("LOADING DATASET")
print("=" * 70)

df = pd.read_excel(INPUT_FILE)

print(f"\nOriginal shape: {df.shape}")


# ============================================================
# CLEAN COLUMN NAMES
# ============================================================

df.columns = (
    df.columns
    .str.strip()
    .str.replace(" ", "_")
    .str.replace(r"[^\w]", "", regex=True)
)

print("\nColumns:")
print(df.columns.tolist())


# ============================================================
# REMOVE DUPLICATES
# ============================================================

before = len(df)

df = df.drop_duplicates()

print(
    f"\nDuplicates removed: {before - len(df)}"
)


# ============================================================
# HANDLE EMPTY VALUES
# ============================================================

df = df.replace(
    [
        "",
        " ",
        "NA",
        "N/A",
        "na",
        "null",
        "NULL",
        "-"
    ],
    np.nan
)


# ============================================================
# TARGET
# ============================================================

TARGET = "Calories_Burned"

if TARGET not in df.columns:
    raise ValueError(
        f"'{TARGET}' column not found!"
    )


# ============================================================
# CONVERT NUMERICAL COLUMNS
# ============================================================

numeric_columns = [
    "Age",
    "Duration_Minutes",
    "Calories_Burned",
    "Heart_Rate_BPM",
    "Workout_Frequency_Per_Week",
    "Sleep_Hours",
    "Water_Intake_Liters",
    "Weight_KG"
]

for column in numeric_columns:

    if column in df.columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )


# ============================================================
# REMOVE INVALID VALUES
# ============================================================

if "Age" in df.columns:
    df.loc[
        (df["Age"] < 1) |
        (df["Age"] > 120),
        "Age"
    ] = np.nan


if "Duration_Minutes" in df.columns:
    df.loc[
        (df["Duration_Minutes"] <= 0),
        "Duration_Minutes"
    ] = np.nan


if "Heart_Rate_BPM" in df.columns:
    df.loc[
        (df["Heart_Rate_BPM"] < 30) |
        (df["Heart_Rate_BPM"] > 250),
        "Heart_Rate_BPM"
    ] = np.nan


if "Weight_KG" in df.columns:
    df.loc[
        (df["Weight_KG"] <= 0) |
        (df["Weight_KG"] > 300),
        "Weight_KG"
    ] = np.nan


if "Sleep_Hours" in df.columns:
    df.loc[
        (df["Sleep_Hours"] < 0) |
        (df["Sleep_Hours"] > 24),
        "Sleep_Hours"
    ] = np.nan


if "Water_Intake_Liters" in df.columns:
    df.loc[
        df["Water_Intake_Liters"] < 0,
        "Water_Intake_Liters"
    ] = np.nan


# ============================================================
# REMOVE ROWS WITHOUT TARGET
# ============================================================

df = df.dropna(
    subset=[TARGET]
)

df = df[
    df[TARGET] >= 0
]


# ============================================================
# REMOVE USER_ID
# ============================================================

if "User_ID" in df.columns:

    df = df.drop(
        columns=["User_ID"]
    )

    print("\nUser_ID removed.")


# ============================================================
# SEPARATE X AND Y
# ============================================================

X = df.drop(
    columns=[TARGET]
)

y = df[TARGET]


# ============================================================
# IDENTIFY FEATURES
# ============================================================

numerical_features = X.select_dtypes(
    include=["number"]
).columns.tolist()

categorical_features = X.select_dtypes(
    include=["object", "category"]
).columns.tolist()


print("\n" + "=" * 70)
print("FEATURES")
print("=" * 70)

print("\nNumerical features:")

for feature in numerical_features:
    print("  -", feature)

print("\nCategorical features:")

for feature in categorical_features:
    print("  -", feature)


# ============================================================
# NUMERICAL PREPROCESSING
# ============================================================

numeric_pipeline = Pipeline(
    steps=[
        (
            "imputer",
            SimpleImputer(
                strategy="median"
            )
        )
    ]
)


# ============================================================
# CATEGORICAL PREPROCESSING
# ============================================================

categorical_pipeline = Pipeline(
    steps=[
        (
            "imputer",
            SimpleImputer(
                strategy="most_frequent"
            )
        ),
        (
            "encoder",
            OneHotEncoder(
                handle_unknown="ignore",
                sparse_output=False
            )
        )
    ]
)


# ============================================================
# COMBINED PREPROCESSOR
# ============================================================

preprocessor = ColumnTransformer(
    transformers=[
        (
            "numerical",
            numeric_pipeline,
            numerical_features
        ),
        (
            "categorical",
            categorical_pipeline,
            categorical_features
        )
    ]
)


# ============================================================
# TRAIN / TEST SPLIT
# ============================================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42
)


print("\n" + "=" * 70)
print("DATA SPLIT")
print("=" * 70)

print(
    f"\nTraining samples: {len(X_train):,}"
)

print(
    f"Testing samples : {len(X_test):,}"
)


# ============================================================
# FIT PREPROCESSOR
# ============================================================

print("\nFitting preprocessing pipeline...")

X_train_processed = preprocessor.fit_transform(
    X_train
)

X_test_processed = preprocessor.transform(
    X_test
)


# ============================================================
# FEATURE NAMES
# ============================================================

feature_names = (
    preprocessor
    .get_feature_names_out()
)


# ============================================================
# CREATE PROCESSED DATASET
# ============================================================

train_processed = pd.DataFrame(
    X_train_processed,
    columns=feature_names,
    index=X_train.index
)

train_processed[TARGET] = y_train


test_processed = pd.DataFrame(
    X_test_processed,
    columns=feature_names,
    index=X_test.index
)

test_processed[TARGET] = y_test


# Combine
processed_df = pd.concat(
    [
        train_processed,
        test_processed
    ]
).sort_index()


# ============================================================
# SAVE DATASET
# ============================================================

processed_df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# SAVE PREPROCESSOR
# ============================================================

joblib.dump(
    preprocessor,
    PREPROCESSOR_FILE
)


# ============================================================
# SAVE FEATURE INFORMATION
# ============================================================

feature_info = {
    "target": TARGET,
    "numerical_features": numerical_features,
    "categorical_features": categorical_features,
    "feature_names": feature_names.tolist()
}

joblib.dump(
    feature_info,
    "trained_models/feature_info.pkl"
)


# ============================================================
# FINAL REPORT
# ============================================================

print("\n" + "=" * 70)
print("PREPROCESSING COMPLETE")
print("=" * 70)

print(
    f"\nOriginal rows : {len(df):,}"
)

print(
    f"Features      : {len(feature_names)}"
)

print(
    f"Training rows : {len(X_train):,}"
)

print(
    f"Testing rows  : {len(X_test):,}"
)

print(
    f"\nProcessed file:"
)

print(
    f"  {OUTPUT_FILE}"
)

print(
    f"\nPreprocessor:"
)

print(
    f"  {PREPROCESSOR_FILE}"
)

print("\nDone!")