"""
Calorie Burn Prediction Script
==============================
This script uses the trained Extra Trees model and preprocessing pipeline
to predict calories burned based on workout and user profile features.

Usage:
------
1. As a Python module:
    >>> from predict import CaloriePredictor
    >>> predictor = CaloriePredictor()
    >>> result = predictor.predict({
    ...     "Age": 28,
    ...     "Gender": "Male",
    ...     "Weight_KG": 75.0,
    ...     "Exercise_Type": "Running",
    ...     "Duration_Minutes": 45,
    ...     "Heart_Rate_BPM": 155,
    ...     "Workout_Frequency_Per_Week": 4,
    ...     "Sleep_Hours": 7.0,
    ...     "Water_Intake_Liters": 2.5,
    ...     "Fitness_Goal": "Weight Loss",
    ...     "Experience_Level": "Intermediate"
    ... })
    >>> print(f"Calories burned: {result:.1f} kcal")

2. Interactive mode:
    $ python predict.py --interactive

3. Run built-in demo examples:
    $ python predict.py --demo

4. CLI single prediction:
    $ python predict.py --age 28 --gender Male --weight 75 --exercise Running --duration 45 --heart-rate 155

5. Batch prediction on a CSV/Excel file:
    $ python predict.py --file new_workouts.csv --output predictions.csv
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Union, Dict, List, Any

import joblib
import numpy as np
import pandas as pd

# Ensure safe console output encoding on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


# Default model paths relative to this script
BASE_DIR = Path(__file__).resolve().parent
DEFAULT_MODEL_DIR = BASE_DIR / "trained_models"
DEFAULT_MODEL_PATH = DEFAULT_MODEL_DIR / "calorie_prediction_model.pkl"
DEFAULT_PREPROCESSOR_PATH = DEFAULT_MODEL_DIR / "preprocessor.pkl"
DEFAULT_FEATURE_INFO_PATH = DEFAULT_MODEL_DIR / "feature_info.pkl"

VALID_EXERCISE_TYPES = [
    "Cycling", "HIIT", "Rowing", "Running", "Swimming",
    "Walking", "Weight Training", "Yoga"
]

VALID_GENDERS = ["Male", "Female"]

VALID_FITNESS_GOALS = [
    "Endurance", "Flexibility", "General Fitness",
    "Muscle Gain", "Weight Loss"
]

VALID_EXPERIENCE_LEVELS = [
    "Beginner", "Intermediate", "Advanced"
]


class CaloriePredictor:
    """Loads trained artifacts and provides prediction methods for raw workout data."""

    def __init__(
        self,
        model_path: Union[str, Path] = DEFAULT_MODEL_PATH,
        preprocessor_path: Union[str, Path] = DEFAULT_PREPROCESSOR_PATH,
        feature_info_path: Union[str, Path] = DEFAULT_FEATURE_INFO_PATH
    ):
        self.model_path = Path(model_path)
        self.preprocessor_path = Path(preprocessor_path)
        self.feature_info_path = Path(feature_info_path)

        self._check_files_exist()

        print(f"Loading preprocessor from: {self.preprocessor_path.name}...")
        self.preprocessor = joblib.load(self.preprocessor_path)

        print(f"Loading prediction model from: {self.model_path.name}...")
        self.model = joblib.load(self.model_path)

        if self.feature_info_path.exists():
            self.feature_info = joblib.load(self.feature_info_path)
        else:
            self.feature_info = None

        # Store expected raw feature columns
        self.numerical_cols = [
            "Age", "Duration_Minutes", "Heart_Rate_BPM",
            "Workout_Frequency_Per_Week", "Sleep_Hours",
            "Water_Intake_Liters", "Weight_KG"
        ]
        self.categorical_cols = [
            "Gender", "Exercise_Type", "Fitness_Goal", "Experience_Level"
        ]
        self.expected_raw_cols = self.numerical_cols + self.categorical_cols

    def _check_files_exist(self):
        missing = []
        if not self.model_path.exists():
            missing.append(str(self.model_path))
        if not self.preprocessor_path.exists():
            missing.append(str(self.preprocessor_path))

        if missing:
            raise FileNotFoundError(
                f"Missing required trained artifact(s):\n" +
                "\n".join(f" - {p}" for p in missing) +
                "\nPlease ensure training completed and files exist in 'trained_models/'."
            )

    @staticmethod
    def _clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
        """Applies exact column name sanitization matching training pipeline."""
        df = df.copy()
        df.columns = (
            df.columns
            .str.strip()
            .str.replace(" ", "_")
            .str.replace(r"[^\w]", "", regex=True)
        )
        return df

    def _normalize_raw_df(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Maps case-insensitive and variation column names to standard feature names.
        """
        df = df.copy()

        # Build alias map
        alias_map = {
            "age": "Age",
            "gender": "Gender",
            "sex": "Gender",
            "weight": "Weight_KG",
            "weight_kg": "Weight_KG",
            "weight(kg)": "Weight_KG",
            "exercise": "Exercise_Type",
            "exercise_type": "Exercise_Type",
            "exercisetype": "Exercise_Type",
            "duration": "Duration_Minutes",
            "duration_minutes": "Duration_Minutes",
            "duration(min)": "Duration_Minutes",
            "duration_min": "Duration_Minutes",
            "heart_rate": "Heart_Rate_BPM",
            "heart_rate_bpm": "Heart_Rate_BPM",
            "heartrate": "Heart_Rate_BPM",
            "bpm": "Heart_Rate_BPM",
            "frequency": "Workout_Frequency_Per_Week",
            "workout_frequency": "Workout_Frequency_Per_Week",
            "workout_frequency_per_week": "Workout_Frequency_Per_Week",
            "frequency_per_week": "Workout_Frequency_Per_Week",
            "sleep": "Sleep_Hours",
            "sleep_hours": "Sleep_Hours",
            "water": "Water_Intake_Liters",
            "water_intake": "Water_Intake_Liters",
            "water_intake_liters": "Water_Intake_Liters",
            "water_liters": "Water_Intake_Liters",
            "goal": "Fitness_Goal",
            "fitness_goal": "Fitness_Goal",
            "experience": "Experience_Level",
            "experience_level": "Experience_Level",
            "level": "Experience_Level"
        }

        rename_dict = {}
        for col in df.columns:
            clean_key = str(col).strip().lower().replace(" ", "_")
            clean_key_nosym = "".join(c for c in clean_key if c.isalnum() or c == "_")
            if clean_key in alias_map:
                rename_dict[col] = alias_map[clean_key]
            elif clean_key_nosym in alias_map:
                rename_dict[col] = alias_map[clean_key_nosym]

        df = df.rename(columns=rename_dict)

        # Ensure numeric types
        for col in self.numerical_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # Fill any missing columns with NaN so the SimpleImputer can impute them
        for col in self.expected_raw_cols:
            if col not in df.columns:
                df[col] = np.nan

        return df[self.expected_raw_cols]

    def _is_preprocessed_data(self, df: pd.DataFrame) -> bool:
        """Checks if input data already has preprocessed prefix columns."""
        sample_cols = [str(c) for c in df.columns[:5]]
        return any(c.startswith("numerical__") or c.startswith("categorical__") for c in sample_cols)

    def predict(
        self,
        data: Union[Dict[str, Any], List[Dict[str, Any]], pd.DataFrame, pd.Series]
    ) -> Union[float, np.ndarray]:
        """
        Predict calories burned for a single workout or batch of workouts.

        Args:
            data: A dictionary, list of dictionaries, pandas Series, or DataFrame
                  containing workout features.

        Returns:
            float if single sample passed, np.ndarray if multiple samples.
        """
        is_single = False

        if isinstance(data, dict):
            df = pd.DataFrame([data])
            is_single = True
        elif isinstance(data, pd.Series):
            df = pd.DataFrame([data.to_dict()])
            is_single = True
        elif isinstance(data, list):
            df = pd.DataFrame(data)
            if len(df) == 1:
                is_single = True
        elif isinstance(data, pd.DataFrame):
            df = data.copy()
            if len(df) == 1:
                is_single = True
        else:
            raise TypeError(
                f"Unsupported data type '{type(data)}'. Pass a dict, list of dicts, or DataFrame."
            )

        # Check if incoming data is already preprocessed or raw
        if self._is_preprocessed_data(df):
            clean_df = self._clean_column_names(df)
            predictions = self.model.predict(clean_df)
        else:
            # Normalize and prepare raw dataframe
            normalized_raw = self._normalize_raw_df(df)

            # Transform raw features using preprocessor
            transformed_arr = self.preprocessor.transform(normalized_raw)
            feature_names = self.preprocessor.get_feature_names_out()

            # Create dataframe and apply column cleaning expected by model
            processed_df = pd.DataFrame(
                transformed_arr,
                columns=feature_names,
                index=normalized_raw.index
            )
            processed_df = self._clean_column_names(processed_df)

            # Model prediction
            predictions = self.model.predict(processed_df)

        if is_single:
            return float(predictions[0])
        return predictions

    def predict_file(
        self,
        input_path: Union[str, Path],
        output_path: Union[str, Path] = None
    ) -> pd.DataFrame:
        """
        Reads a CSV or Excel file, generates predictions, and optionally saves the output.
        """
        input_path = Path(input_path)
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")

        print(f"\nReading dataset from {input_path}...")
        if input_path.suffix.lower() in [".xlsx", ".xls"]:
            df = pd.read_excel(input_path)
        else:
            df = pd.read_csv(input_path)

        print(f"Loaded {len(df):,} rows. Generating predictions...")
        preds = self.predict(df)
        df["Predicted_Calories_Burned"] = np.round(preds, 2)

        if output_path:
            output_path = Path(output_path)
            if output_path.suffix.lower() in [".xlsx", ".xls"]:
                df.to_excel(output_path, index=False)
            else:
                df.to_csv(output_path, index=False)
            print(f"Saved predictions to: {output_path}")

        return df


def predict_single_workout(
    age: float = 25.0,
    gender: str = "Male",
    weight_kg: float = 70.0,
    exercise_type: str = "Running",
    duration_minutes: float = 45.0,
    heart_rate_bpm: float = 145.0,
    workout_frequency_per_week: float = 4.0,
    sleep_hours: float = 7.5,
    water_intake_liters: float = 2.5,
    fitness_goal: str = "Weight Loss",
    experience_level: str = "Intermediate",
    predictor: CaloriePredictor = None
) -> float:
    """Helper function to predict calories burned for a single workout."""
    if predictor is None:
        predictor = CaloriePredictor()

    data = {
        "Age": age,
        "Gender": gender,
        "Weight_KG": weight_kg,
        "Exercise_Type": exercise_type,
        "Duration_Minutes": duration_minutes,
        "Heart_Rate_BPM": heart_rate_bpm,
        "Workout_Frequency_Per_Week": workout_frequency_per_week,
        "Sleep_Hours": sleep_hours,
        "Water_Intake_Liters": water_intake_liters,
        "Fitness_Goal": fitness_goal,
        "Experience_Level": experience_level
    }
    return predictor.predict(data)


def run_interactive():
    """Runs a friendly terminal prompt for predicting calorie burn."""
    print("\n" + "=" * 65)
    print("      WORKOUT CALORIE BURN PREDICTOR - INTERACTIVE MODE")
    print("=" * 65)
    print("Press Enter to accept the default value in brackets [].\n")

    def prompt(text, default, val_type=str, choices=None):
        while True:
            choice_str = f" ({'/'.join(choices)})" if choices else ""
            raw = input(f" - {text}{choice_str} [{default}]: ").strip()
            if not raw:
                return default
            if choices:
                matches = [c for c in choices if c.lower() == raw.lower()]
                if matches:
                    return matches[0]
                print(f"  [!] Invalid choice. Please select from: {', '.join(choices)}")
                continue
            try:
                return val_type(raw)
            except ValueError:
                print(f"  [!] Please enter a valid {val_type.__name__}.")

    age = prompt("Age", 28, int)
    gender = prompt("Gender", "Male", str, VALID_GENDERS)
    weight = prompt("Weight (kg)", 75.0, float)
    exercise = prompt("Exercise Type", "Running", str, VALID_EXERCISE_TYPES)
    duration = prompt("Duration (minutes)", 45.0, float)
    heart_rate = prompt("Heart Rate (BPM)", 150.0, float)
    frequency = prompt("Workout Frequency (days/week)", 4, int)
    sleep = prompt("Sleep Hours", 7.0, float)
    water = prompt("Water Intake (liters)", 2.5, float)
    goal = prompt("Fitness Goal", "Weight Loss", str, VALID_FITNESS_GOALS)
    experience = prompt("Experience Level", "Intermediate", str, VALID_EXPERIENCE_LEVELS)

    workout_data = {
        "Age": age,
        "Gender": gender,
        "Weight_KG": weight,
        "Exercise_Type": exercise,
        "Duration_Minutes": duration,
        "Heart_Rate_BPM": heart_rate,
        "Workout_Frequency_Per_Week": frequency,
        "Sleep_Hours": sleep,
        "Water_Intake_Liters": water,
        "Fitness_Goal": goal,
        "Experience_Level": experience
    }

    print("\nLoading model & calculating prediction...")
    predictor = CaloriePredictor()
    calories = predictor.predict(workout_data)
    burn_rate = calories / duration if duration > 0 else 0.0

    print("\n" + "=" * 65)
    print("                   PREDICTION RESULT")
    print("=" * 65)
    print(f" Workout Profile:")
    print(f"  - User        : {gender}, {age} yrs, {weight:.1f} kg")
    print(f"  - Exercise    : {exercise} ({duration:.0f} mins @ {heart_rate:.0f} BPM)")
    print(f"  - Lifestyle   : {frequency} workouts/wk | {sleep:.1f}h sleep | {water:.1f}L water")
    print(f"  - Profile     : {experience} level | Goal: {goal}")
    print("-" * 65)
    print(f"  [+] ESTIMATED CALORIES BURNED : {calories:.1f} kcal")
    print(f"  [*] BURN RATE                 : {burn_rate:.1f} kcal/min")
    print("=" * 65 + "\n")


def run_demo():
    """Runs prediction on 3 distinct workout scenarios to demonstrate capability."""
    print("\n" + "=" * 75)
    print("               RUNNING CALORIE PREDICTION DEMO")
    print("=" * 75)

    scenarios = [
        {
            "name": "High Intensity Morning HIIT",
            "Age": 26,
            "Gender": "Female",
            "Weight_KG": 62.0,
            "Exercise_Type": "HIIT",
            "Duration_Minutes": 30.0,
            "Heart_Rate_BPM": 168.0,
            "Workout_Frequency_Per_Week": 5,
            "Sleep_Hours": 7.5,
            "Water_Intake_Liters": 3.0,
            "Fitness_Goal": "Weight Loss",
            "Experience_Level": "Advanced"
        },
        {
            "name": "Evening Endurance Cycling",
            "Age": 34,
            "Gender": "Male",
            "Weight_KG": 82.0,
            "Exercise_Type": "Cycling",
            "Duration_Minutes": 60.0,
            "Heart_Rate_BPM": 142.0,
            "Workout_Frequency_Per_Week": 3,
            "Sleep_Hours": 6.5,
            "Water_Intake_Liters": 2.2,
            "Fitness_Goal": "Endurance",
            "Experience_Level": "Intermediate"
        },
        {
            "name": "Gentle Recovery Yoga",
            "Age": 45,
            "Gender": "Female",
            "Weight_KG": 58.0,
            "Exercise_Type": "Yoga",
            "Duration_Minutes": 45.0,
            "Heart_Rate_BPM": 105.0,
            "Workout_Frequency_Per_Week": 3,
            "Sleep_Hours": 8.0,
            "Water_Intake_Liters": 2.0,
            "Fitness_Goal": "Flexibility",
            "Experience_Level": "Beginner"
        }
    ]

    predictor = CaloriePredictor()

    results = []
    for sc in scenarios:
        name = sc["name"]
        pred = predictor.predict(sc)
        rate = pred / sc["Duration_Minutes"]
        results.append({
            "Scenario": name,
            "Exercise": sc["Exercise_Type"],
            "Duration": f"{sc['Duration_Minutes']:.0f} min",
            "Heart Rate": f"{sc['Heart_Rate_BPM']:.0f} bpm",
            "Predicted Calories": f"{pred:.1f} kcal",
            "Burn Rate": f"{rate:.1f} kcal/min"
        })

    demo_df = pd.DataFrame(results)
    print("\nDemo Predictions:")
    print("-" * 75)
    print(demo_df.to_string(index=False))
    print("=" * 75 + "\n")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Predict calories burned from workout features using trained Extra Trees model."
    )
    parser.add_argument("--demo", action="store_true", help="Run demo with example workouts")
    parser.add_argument("--interactive", action="store_true", help="Run interactive CLI prompts")
    parser.add_argument("--file", type=str, help="Input CSV or Excel file for batch prediction")
    parser.add_argument("--output", type=str, help="Output CSV or Excel file to save batch predictions")

    # Single prediction optional args
    parser.add_argument("--age", type=float, help="Age in years")
    parser.add_argument("--gender", type=str, choices=VALID_GENDERS, help="Gender (Male / Female)")
    parser.add_argument("--weight", type=float, help="Body weight in KG")
    parser.add_argument("--exercise", type=str, choices=VALID_EXERCISE_TYPES, help="Exercise type")
    parser.add_argument("--duration", type=float, help="Duration in minutes")
    parser.add_argument("--heart-rate", type=float, help="Average heart rate in BPM")
    parser.add_argument("--frequency", type=int, help="Workouts per week (1-7)")
    parser.add_argument("--sleep", type=float, help="Daily sleep in hours")
    parser.add_argument("--water", type=float, help="Daily water intake in liters")
    parser.add_argument("--goal", type=str, choices=VALID_FITNESS_GOALS, help="Fitness goal")
    parser.add_argument("--experience", type=str, choices=VALID_EXPERIENCE_LEVELS, help="Experience level")

    return parser.parse_args()


def main():
    args = parse_args()

    # 1. Demo mode
    if args.demo:
        run_demo()
        return

    # 2. Batch file mode
    if args.file:
        predictor = CaloriePredictor()
        predictor.predict_file(args.file, args.output)
        return

    # 3. Direct CLI arguments
    cli_flags = [args.age, args.gender, args.weight, args.exercise, args.duration, args.heart_rate]
    if any(cli_flags):
        workout_data = {
            "Age": args.age if args.age is not None else 28,
            "Gender": args.gender if args.gender is not None else "Male",
            "Weight_KG": args.weight if args.weight is not None else 75.0,
            "Exercise_Type": args.exercise if args.exercise is not None else "Running",
            "Duration_Minutes": args.duration if args.duration is not None else 45.0,
            "Heart_Rate_BPM": args.heart_rate if args.heart_rate is not None else 150.0,
            "Workout_Frequency_Per_Week": args.frequency if args.frequency is not None else 4,
            "Sleep_Hours": args.sleep if args.sleep is not None else 7.0,
            "Water_Intake_Liters": args.water if args.water is not None else 2.5,
            "Fitness_Goal": args.goal if args.goal is not None else "Weight Loss",
            "Experience_Level": args.experience if args.experience is not None else "Intermediate"
        }
        predictor = CaloriePredictor()
        calories = predictor.predict(workout_data)
        dur = workout_data["Duration_Minutes"]
        rate = calories / dur if dur > 0 else 0
        print("\n" + "=" * 55)
        print(f"[+] Predicted Calories Burned : {calories:.1f} kcal")
        print(f"[*] Burn Rate                 : {rate:.1f} kcal/min")
        print("=" * 55 + "\n")
        return

    # 4. Interactive mode (default if no arguments)
    run_interactive()


if __name__ == "__main__":
    main()
