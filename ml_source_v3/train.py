import os
import joblib
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split, KFold, cross_val_score
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


# ============================================================
# CONFIGURATION
# ============================================================

DATASET = "preprocessed_workout_dataset.csv"

MODEL_DIR = "trained_models"

MODEL_FILE = os.path.join(
    MODEL_DIR,
    "calorie_prediction_model.pkl"
)

FEATURE_FILE = os.path.join(
    MODEL_DIR,
    "model_features.pkl"
)

os.makedirs(MODEL_DIR, exist_ok=True)


# ============================================================
# LOAD DATASET
# ============================================================

print("=" * 75)
print("LOADING DATASET")
print("=" * 75)

df = pd.read_csv(DATASET)

print(f"\nDataset shape: {df.shape}")


# ============================================================
# CLEAN COLUMN NAMES
# ============================================================

df.columns = (
    df.columns
    .str.strip()
    .str.replace(" ", "_")
    .str.replace(r"[^\w]", "", regex=True)
)


# ============================================================
# TARGET
# ============================================================

TARGET = "Calories_Burned"

if TARGET not in df.columns:
    raise ValueError(
        f"Target column '{TARGET}' not found!"
    )


# ============================================================
# REMOVE DUPLICATES
# ============================================================

before = len(df)

df = df.drop_duplicates()

print(
    f"Duplicates removed: {before - len(df)}"
)


# ============================================================
# HANDLE MISSING VALUES
# ============================================================

df = df.replace(
    ["", " ", "NA", "N/A", "null", "NULL", "-"],
    np.nan
)

df[TARGET] = pd.to_numeric(
    df[TARGET],
    errors="coerce"
)

df = df.dropna(
    subset=[TARGET]
)


# ============================================================
# FEATURES / TARGET
# ============================================================

X = df.drop(
    columns=[TARGET]
)

y = df[TARGET]


# ============================================================
# REMOVE USER ID
# ============================================================

if "User_ID" in X.columns:

    X = X.drop(
        columns=["User_ID"]
    )

    print("\nUser_ID removed.")


# ============================================================
# DETECT FEATURES
# ============================================================

categorical_features = X.select_dtypes(
    include=["object", "category"]
).columns.tolist()

numerical_features = X.select_dtypes(
    include=["number"]
).columns.tolist()


print("\n" + "=" * 75)
print("FEATURES")
print("=" * 75)

print("\nNumerical:")

for feature in numerical_features:
    print("  ", feature)

print("\nCategorical:")

for feature in categorical_features:
    print("  ", feature)


# ============================================================
# NUMERICAL PIPELINE
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
# CATEGORICAL PIPELINE
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
# PREPROCESSOR
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
# EXTRA TREES MODEL
# ============================================================

model = ExtraTreesRegressor(
    n_estimators=300,
    max_depth=None,
    min_samples_split=2,
    min_samples_leaf=1,
    max_features=1.0,
    random_state=42,
    n_jobs=-1
)


# ============================================================
# COMPLETE PIPELINE
# ============================================================

pipeline = Pipeline(
    steps=[
        (
            "preprocessor",
            preprocessor
        ),
        (
            "model",
            model
        )
    ]
)


# ============================================================
# TRAIN / TEST SPLIT
# ============================================================

print("\n" + "=" * 75)
print("TRAIN / TEST SPLIT")
print("=" * 75)

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42
)

print(
    f"\nTraining samples: {len(X_train):,}"
)

print(
    f"Testing samples : {len(X_test):,}"
)


# ============================================================
# TRAIN
# ============================================================

print("\n" + "=" * 75)
print("TRAINING EXTRA TREES")
print("=" * 75)

pipeline.fit(
    X_train,
    y_train
)

print("\nTraining completed!")


# ============================================================
# TEST
# ============================================================

print("\n" + "=" * 75)
print("MODEL TESTING")
print("=" * 75)

y_pred = pipeline.predict(
    X_test
)


# ============================================================
# METRICS
# ============================================================

mae = mean_absolute_error(
    y_test,
    y_pred
)

rmse = np.sqrt(
    mean_squared_error(
        y_test,
        y_pred
    )
)

r2 = r2_score(
    y_test,
    y_pred
)


print("\nTest Performance")
print("-" * 50)

print(
    f"R²            : {r2:.4f}"
)

print(
    f"R² Percentage : {r2 * 100:.2f}%"
)

print(
    f"MAE           : {mae:.2f} calories"
)

print(
    f"RMSE          : {rmse:.2f} calories"
)


# ============================================================
# 5-FOLD CROSS VALIDATION
# ============================================================

print("\n" + "=" * 75)
print("5-FOLD CROSS VALIDATION")
print("=" * 75)

kf = KFold(
    n_splits=5,
    shuffle=True,
    random_state=42
)

cv_scores = cross_val_score(
    pipeline,
    X_train,
    y_train,
    cv=kf,
    scoring="r2",
    n_jobs=-1
)


print("\nIndividual fold scores:")

for i, score in enumerate(
    cv_scores,
    start=1
):

    print(
        f"Fold {i}: "
        f"{score:.4f} "
        f"({score * 100:.2f}%)"
    )


cv_mean = cv_scores.mean()
cv_std = cv_scores.std()


print(
    f"\nMean CV R² : {cv_mean:.4f}"
)

print(
    f"Mean CV %   : {cv_mean * 100:.2f}%"
)

print(
    f"CV Std      : {cv_std:.4f}"
)


# ============================================================
# TRAIN FINAL MODEL
# ============================================================

print("\n" + "=" * 75)
print("FINAL MODEL TRAINING")
print("=" * 75)

print(
    f"\nTraining on all {len(X):,} samples..."
)

pipeline.fit(
    X,
    y
)

print("Final model trained!")


# ============================================================
# SAVE MODEL
# ============================================================

joblib.dump(
    pipeline,
    MODEL_FILE
)


# ============================================================
# SAVE MODEL INFORMATION
# ============================================================

model_info = {

    "algorithm":
        "Extra Trees Regressor",

    "n_estimators":
        300,

    "target":
        TARGET,

    "features":
        X.columns.tolist(),

    "numerical_features":
        numerical_features,

    "categorical_features":
        categorical_features,

    "test_r2":
        r2,

    "test_mae":
        mae,

    "test_rmse":
        rmse,

    "cv_mean_r2":
        cv_mean,

    "cv_std":
        cv_std,

    "random_state":
        42
}


joblib.dump(
    model_info,
    FEATURE_FILE
)


# ============================================================
# FINAL REPORT
# ============================================================

print("\n")
print("=" * 75)
print("MODEL TRAINING COMPLETE")
print("=" * 75)

print("\nDataset")
print("-" * 50)

print(
    f"Total samples : {len(df):,}"
)

print(
    f"Features      : {len(X.columns)}"
)


print("\nModel")
print("-" * 50)

print(
    "Algorithm     : Extra Trees Regressor"
)

print(
    "Trees         : 300"
)


print("\nTest Performance")
print("-" * 50)

print(
    f"R²            : {r2:.4f}"
)

print(
    f"R² Percentage : {r2 * 100:.2f}%"
)

print(
    f"MAE           : {mae:.2f} calories"
)

print(
    f"RMSE          : {rmse:.2f} calories"
)


print("\n5-Fold Cross Validation")
print("-" * 50)

print(
    f"Mean R²       : {cv_mean:.4f}"
)

print(
    f"Mean CV %     : {cv_mean * 100:.2f}%"
)

print(
    f"CV Std        : {cv_std:.4f}"
)


print("\nSaved files")
print("-" * 50)

print(
    f"Model         : {MODEL_FILE}"
)

print(
    f"Features      : {FEATURE_FILE}"
)

print("\n" + "=" * 75)
print("DONE")
print("=" * 75)