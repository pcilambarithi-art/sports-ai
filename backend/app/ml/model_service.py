r"""
Singleton service integrating the user's existing trained ExtraTreesRegressor
model and dataset from D:\V3 (configured via environment variables).

IMPORTANT:
- Never retrains, overwrites, or replaces the user's trained model.
- Uses the exact preprocessing pipeline from trained_models/preprocessor.pkl
  and exact column sanitization matching D:\V3\predict.py.
- Computes real ensemble uncertainty across all 300 trees, real global feature
  importances, real counterfactual sensitivity explanations, and real dataset
  percentile benchmarks from preprocessed_workout_dataset.csv.
"""

from __future__ import annotations

import logging
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import joblib
import numpy as np
import pandas as pd

from app.core.config import settings

logger = logging.getLogger(__name__)

VALID_EXERCISE_TYPES = [
    "Cycling",
    "HIIT",
    "Rowing",
    "Running",
    "Swimming",
    "Walking",
    "Weight Training",
    "Yoga",
]

VALID_GENDERS = ["Male", "Female"]

VALID_FITNESS_GOALS = [
    "Endurance",
    "Flexibility",
    "General Fitness",
    "Muscle Gain",
    "Weight Loss",
]

VALID_EXPERIENCE_LEVELS = ["Beginner", "Intermediate", "Advanced"]

NUMERICAL_COLS = [
    "Age",
    "Duration_Minutes",
    "Heart_Rate_BPM",
    "Workout_Frequency_Per_Week",
    "Sleep_Hours",
    "Water_Intake_Liters",
    "Weight_KG",
]

CATEGORICAL_COLS = [
    "Gender",
    "Exercise_Type",
    "Fitness_Goal",
    "Experience_Level",
]

EXPECTED_RAW_COLS = NUMERICAL_COLS + CATEGORICAL_COLS

ALIAS_MAP = {
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
    "level": "Experience_Level",
}


class ModelNotReadyError(RuntimeError):
    """Raised when inference is requested while the 2.93 GB model is still loading or unavailable."""


class CalorieModelService:
    """Thread-safe singleton managing the existing trained model and dataset benchmarks."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self.status: str = "idle"  # idle | loading | ready | error
        self.error_message: Optional[str] = None
        self.load_started_at: Optional[float] = None
        self.load_time_seconds: Optional[float] = None

        self.preprocessor = None
        self.model = None
        self.model_features: Dict[str, Any] = {}
        self.feature_info: Dict[str, Any] = {}
        self.global_feature_importances: List[Dict[str, Any]] = []
        self.dataset_stats: Dict[str, Any] = {}
        self._exercise_calorie_arrays: Dict[str, np.ndarray] = {}
        self._all_calories_array: Optional[np.ndarray] = None

    def initialize_metadata_and_benchmarks(self) -> None:
        """Fast synchronous load (<1s) of small metadata artifacts and dataset distributions."""
        with self._lock:
            try:
                if settings.model_features_path.exists():
                    self.model_features = joblib.load(settings.model_features_path)
                if settings.feature_info_path.exists():
                    self.feature_info = joblib.load(settings.feature_info_path)
                if settings.preprocessor_path.exists():
                    self.preprocessor = joblib.load(settings.preprocessor_path)
            except Exception as exc:
                logger.exception("Failed to load model metadata/preprocessor: %s", exc)
                self.error_message = str(exc)

            self._load_dataset_benchmarks()

    def _load_dataset_benchmarks(self) -> None:
        ds_path = settings.dataset_file_path
        if not ds_path.exists():
            logger.warning("Dataset benchmark file not found at %s", ds_path)
            return
        try:
            df = pd.read_csv(ds_path)
            if "Calories_Burned" not in df.columns:
                return

            all_cals = np.sort(df["Calories_Burned"].dropna().to_numpy(dtype=float))
            self._all_calories_array = all_cals

            by_exercise: Dict[str, Dict[str, Any]] = {}
            for ex in VALID_EXERCISE_TYPES:
                col_a = f"categorical__Exercise_Type_{ex}"
                col_b = f"categorical__Exercise_Type_{ex.replace(' ', '_')}"
                col = col_a if col_a in df.columns else (col_b if col_b in df.columns else None)
                if col:
                    sub = df[df[col] == 1.0]
                    if len(sub) > 0:
                        cals = np.sort(sub["Calories_Burned"].to_numpy(dtype=float))
                        self._exercise_calorie_arrays[ex] = cals
                        dur = sub["numerical__Duration_Minutes"].to_numpy(dtype=float)
                        rates = sub["Calories_Burned"].to_numpy(dtype=float) / np.maximum(dur, 1.0)
                        by_exercise[ex] = {
                            "count": int(len(sub)),
                            "mean_calories": round(float(cals.mean()), 2),
                            "median_calories": round(float(np.median(cals)), 2),
                            "p25_calories": round(float(np.percentile(cals, 25)), 2),
                            "p75_calories": round(float(np.percentile(cals, 75)), 2),
                            "p90_calories": round(float(np.percentile(cals, 90)), 2),
                            "mean_burn_rate": round(float(rates.mean()), 2),
                            "mean_hr": round(float(sub["numerical__Heart_Rate_BPM"].mean()), 1),
                            "mean_duration": round(float(dur.mean()), 1),
                        }

            num_ranges = {}
            for col in NUMERICAL_COLS:
                prefixed = f"numerical__{col}"
                if prefixed in df.columns:
                    s = df[prefixed]
                    num_ranges[col] = {
                        "min": round(float(s.min()), 2),
                        "max": round(float(s.max()), 2),
                        "mean": round(float(s.mean()), 2),
                        "median": round(float(s.median()), 2),
                    }

            self.dataset_stats = {
                "dataset_path": str(ds_path),
                "total_rows": int(len(df)),
                "feature_count": int(len(df.columns) - 1),
                "target": "Calories_Burned",
                "target_summary": {
                    "min": round(float(all_cals.min()), 2),
                    "max": round(float(all_cals.max()), 2),
                    "mean": round(float(all_cals.mean()), 2),
                    "std": round(float(all_cals.std()), 2),
                    "median": round(float(np.median(all_cals)), 2),
                    "p25": round(float(np.percentile(all_cals, 25)), 2),
                    "p75": round(float(np.percentile(all_cals, 75)), 2),
                },
                "by_exercise": by_exercise,
                "numerical_ranges": num_ranges,
            }
            logger.info("Loaded dataset benchmark statistics from %s (%d rows)", ds_path, len(df))
        except Exception as exc:
            logger.exception("Failed loading dataset statistics: %s", exc)

    def start_background_load(self) -> None:
        """Load the 2.93 GB trained model asynchronously so API boots immediately."""
        with self._lock:
            if self.status in {"loading", "ready"}:
                return
            self.status = "loading"
            self.error_message = None
            self.load_started_at = time.time()

        t = threading.Thread(target=self._load_model_worker, name="ml-model-loader", daemon=True)
        t.start()

    def load_sync(self) -> None:
        """Synchronously load the trained model (used if explicitly triggered or in tests)."""
        self._load_model_worker()

    def _load_model_worker(self) -> None:
        t0 = time.time()
        try:
            model_path = settings.model_path
            prep_path = settings.preprocessor_path
            if not model_path.exists():
                raise FileNotFoundError(f"Trained model file not found: {model_path}")
            if not prep_path.exists():
                raise FileNotFoundError(f"Preprocessor file not found: {prep_path}")

            logger.info("Loading existing trained model from %s ...", model_path)
            preprocessor = joblib.load(prep_path)
            model = joblib.load(model_path)

            # Extract real feature importances from ExtraTreesRegressor
            importances_list: List[Dict[str, Any]] = []
            try:
                est = model.named_steps["model"]
                feat_names = list(self.model_features.get("features", []))
                if not feat_names and self.feature_info:
                    feat_names = [
                        c.strip().replace(" ", "_")
                        for c in self.feature_info.get("feature_names", [])
                    ]
                imps = getattr(est, "feature_importances_", None)
                if imps is not None and len(feat_names) == len(imps):
                    paired = sorted(zip(feat_names, imps), key=lambda x: x[1], reverse=True)
                    for fname, imp in paired:
                        clean_label = (
                            fname.replace("numerical__", "")
                            .replace("categorical__", "")
                            .replace("_", " ")
                        )
                        importances_list.append(
                            {
                                "feature": fname,
                                "label": clean_label,
                                "importance": round(float(imp), 5),
                                "importance_pct": round(float(imp) * 100.0, 2),
                            }
                        )
            except Exception as imp_exc:
                logger.warning("Could not extract feature importances: %s", imp_exc)

            elapsed = time.time() - t0
            with self._lock:
                self.preprocessor = preprocessor
                self.model = model
                self.global_feature_importances = importances_list
                self.load_time_seconds = round(elapsed, 2)
                self.status = "ready"
                self.error_message = None

            logger.info("Trained model loaded and ready in %.2fs", elapsed)
        except Exception as exc:
            logger.exception("Error loading trained model: %s", exc)
            with self._lock:
                self.status = "error"
                self.error_message = str(exc)

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            elapsed_loading = (
                round(time.time() - self.load_started_at, 1)
                if self.status == "loading" and self.load_started_at
                else None
            )
            mf = self.model_features or {}
            return {
                "status": self.status,
                "ready": self.status == "ready" and self.model is not None,
                "error": self.error_message,
                "load_time_seconds": self.load_time_seconds,
                "loading_elapsed_seconds": elapsed_loading,
                "model_path": str(settings.model_path),
                "model_file_exists": settings.model_path.exists(),
                "model_size_gb": (
                    round(settings.model_path.stat().st_size / (1024**3), 2)
                    if settings.model_path.exists()
                    else None
                ),
                "preprocessor_path": str(settings.preprocessor_path),
                "algorithm": mf.get("algorithm", "Extra Trees Regressor"),
                "n_estimators": mf.get("n_estimators", 300),
                "target": mf.get("target", "Calories_Burned"),
                "metrics": {
                    "test_r2": round(float(mf["test_r2"]), 4) if "test_r2" in mf else None,
                    "test_r2_pct": round(float(mf["test_r2"]) * 100, 2) if "test_r2" in mf else None,
                    "test_mae": round(float(mf["test_mae"]), 2) if "test_mae" in mf else None,
                    "test_rmse": round(float(mf["test_rmse"]), 2) if "test_rmse" in mf else None,
                    "cv_mean_r2": round(float(mf["cv_mean_r2"]), 4) if "cv_mean_r2" in mf else None,
                    "cv_std": round(float(mf["cv_std"]), 4) if "cv_std" in mf else None,
                },
                "supported_inputs": {
                    "numerical": NUMERICAL_COLS,
                    "categorical": {
                        "Gender": VALID_GENDERS,
                        "Exercise_Type": VALID_EXERCISE_TYPES,
                        "Fitness_Goal": VALID_FITNESS_GOALS,
                        "Experience_Level": VALID_EXPERIENCE_LEVELS,
                    },
                },
                "global_feature_importances": self.global_feature_importances[:12],
                "limitations": [
                    "Trained specifically for tabular workout calorie expenditure regression (Calories_Burned).",
                    "Does not directly process video frames, pose keypoints, clinical injury diagnostics, or opponent game statistics.",
                    "Trained on Age 18-60, Duration 15-120 min, Heart Rate 90-180 BPM, Weight 45-120 kg; inputs outside these ranges are extrapolated.",
                ],
            }

    @staticmethod
    def _clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df.columns = (
            df.columns.str.strip()
            .str.replace(" ", "_")
            .str.replace(r"[^\w]", "", regex=True)
        )
        return df

    @staticmethod
    def _normalize_raw_df(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        rename_dict = {}
        for col in df.columns:
            clean_key = str(col).strip().lower().replace(" ", "_")
            clean_key_nosym = "".join(c for c in clean_key if c.isalnum() or c == "_")
            if clean_key in ALIAS_MAP:
                rename_dict[col] = ALIAS_MAP[clean_key]
            elif clean_key_nosym in ALIAS_MAP:
                rename_dict[col] = ALIAS_MAP[clean_key_nosym]
        df = df.rename(columns=rename_dict)

        for col in NUMERICAL_COLS:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        for col in EXPECTED_RAW_COLS:
            if col not in df.columns:
                df[col] = np.nan

        return df[EXPECTED_RAW_COLS]

    def _transform_raw_to_model_df(self, df: pd.DataFrame) -> pd.DataFrame:
        normalized_raw = self._normalize_raw_df(df)
        transformed_arr = self.preprocessor.transform(normalized_raw)
        feature_names = self.preprocessor.get_feature_names_out()
        processed_df = pd.DataFrame(
            transformed_arr,
            columns=feature_names,
            index=normalized_raw.index,
        )
        return self._clean_column_names(processed_df)

    def _compute_dataset_percentile(self, calories: float, exercise_type: str) -> Optional[float]:
        arr = self._exercise_calorie_arrays.get(exercise_type)
        if arr is None or len(arr) == 0:
            arr = self._all_calories_array
        if arr is None or len(arr) == 0:
            return None
        rank = int(np.searchsorted(arr, calories, side="right"))
        return round(100.0 * rank / len(arr), 1)

    def _ensure_ready(self) -> None:
        if self.status != "ready" or self.model is None or self.preprocessor is None:
            if self.status == "loading":
                elapsed = (
                    round(time.time() - self.load_started_at, 1)
                    if self.load_started_at
                    else 0.0
                )
                raise ModelNotReadyError(
                    f"Trained model (2.93 GB) is currently loading into memory ({elapsed}s elapsed). "
                    "Please retry in a few moments."
                )
            raise ModelNotReadyError(
                f"Trained model is not ready (status={self.status}, error={self.error_message})."
            )

    def predict_single(
        self,
        raw_input: Dict[str, Any],
        include_what_if: bool = True,
    ) -> Dict[str, Any]:
        """Run real inference with 300-tree uncertainty interval and real what-if explanations."""
        self._ensure_ready()

        df_in = pd.DataFrame([raw_input])
        processed_df = self._transform_raw_to_model_df(df_in)

        # Primary prediction from trained pipeline
        prediction = float(self.model.predict(processed_df)[0])

        # Real tree-level ensemble distribution across all 300 ExtraTrees estimators
        X_internal = self.model.named_steps["preprocessor"].transform(processed_df)
        est = self.model.named_steps["model"]
        tree_preds = np.array([tree.predict(X_internal)[0] for tree in est.estimators_], dtype=float)
        ensemble_std = float(tree_preds.std())
        p10 = float(np.percentile(tree_preds, 10))
        p90 = float(np.percentile(tree_preds, 90))
        # Relative consistency indicator derived purely from ensemble dispersion (CV)
        rel_dispersion = ensemble_std / max(prediction, 1.0)
        ensemble_agreement_pct = round(max(0.0, min(100.0, (1.0 - rel_dispersion) * 100.0)), 1)

        duration = float(raw_input.get("Duration_Minutes", 0) or 0)
        burn_rate = round(prediction / duration, 2) if duration > 0 else 0.0
        exercise_type = str(raw_input.get("Exercise_Type", "Running"))
        percentile = self._compute_dataset_percentile(prediction, exercise_type)

        # Check range warnings against training data distribution
        range_warnings: List[str] = []
        ranges = self.dataset_stats.get("numerical_ranges", {})
        for col in NUMERICAL_COLS:
            val = raw_input.get(col)
            if val is not None and col in ranges:
                r = ranges[col]
                if float(val) < r["min"] or float(val) > r["max"]:
                    range_warnings.append(
                        f"{col.replace('_', ' ')} ({val}) is outside training dataset range [{r['min']} - {r['max']}]."
                    )

        # Real counterfactual sensitivity ("what-if") by calling the actual trained model
        what_if_scenarios: List[Dict[str, Any]] = []
        if include_what_if:
            variants = []
            if duration + 15 <= 120:
                v = dict(raw_input)
                v["Duration_Minutes"] = duration + 15
                variants.append(("Duration +15 min", v))
            elif duration - 15 >= 15:
                v = dict(raw_input)
                v["Duration_Minutes"] = duration - 15
                variants.append(("Duration -15 min", v))

            hr = float(raw_input.get("Heart_Rate_BPM", 140))
            if hr + 12 <= 180:
                v = dict(raw_input)
                v["Heart_Rate_BPM"] = hr + 12
                variants.append(("Heart Rate +12 BPM", v))

            alt_exercises = [ex for ex in ["HIIT", "Running", "Cycling", "Swimming"] if ex != exercise_type][:2]
            for alt_ex in alt_exercises:
                v = dict(raw_input)
                v["Exercise_Type"] = alt_ex
                variants.append((f"Switch to {alt_ex}", v))

            if variants:
                var_df = pd.DataFrame([v for _, v in variants])
                var_proc = self._transform_raw_to_model_df(var_df)
                var_preds = self.model.predict(var_proc)
                for (label, _), vp in zip(variants, var_preds):
                    delta = float(vp) - prediction
                    what_if_scenarios.append(
                        {
                            "scenario": label,
                            "predicted_calories": round(float(vp), 2),
                            "delta_calories": round(delta, 2),
                        }
                    )

        # Human-readable, data-grounded explanation
        ex_bench = self.dataset_stats.get("by_exercise", {}).get(exercise_type)
        summary_points = [
            f"Predicted {prediction:.1f} kcal ({burn_rate:.2f} kcal/min) using the trained 300-tree ExtraTreesRegressor pipeline.",
            f"Across all 300 decision trees, 80% of estimates fall between {p10:.1f} and {p90:.1f} kcal (std: ±{ensemble_std:.1f} kcal).",
        ]
        if ex_bench:
            diff_vs_avg = prediction - ex_bench["mean_calories"]
            direction = "above" if diff_vs_avg >= 0 else "below"
            summary_points.append(
                f"This output is {abs(diff_vs_avg):.1f} kcal {direction} the {exercise_type} dataset average ({ex_bench['mean_calories']:.1f} kcal; {percentile}th percentile of {ex_bench['count']:,} training samples)."
            )
        if self.global_feature_importances:
            top3 = ", ".join(
                f"{item['label']} ({item['importance_pct']}%)"
                for item in self.global_feature_importances[:3]
            )
            summary_points.append(f"Top global model drivers: {top3}.")

        return {
            "predicted_calories": round(prediction, 2),
            "burn_rate_per_min": burn_rate,
            "ensemble_std": round(ensemble_std, 2),
            "confidence_low": round(p10, 2),
            "confidence_high": round(p90, 2),
            "ensemble_agreement_pct": ensemble_agreement_pct,
            "dataset_percentile": percentile,
            "exercise_benchmark": ex_bench,
            "model_version": f"{self.model_features.get('algorithm', 'Extra Trees Regressor')} ({self.model_features.get('n_estimators', 300)} trees)",
            "explanation": {
                "summary_points": summary_points,
                "top_global_drivers": self.global_feature_importances[:6],
                "what_if_scenarios": what_if_scenarios,
                "range_warnings": range_warnings,
            },
        }

    def predict_batch_fast(self, rows: List[Dict[str, Any]]) -> List[float]:
        """Fast batch prediction for training plan generation or CSV batch scoring."""
        self._ensure_ready()
        if not rows:
            return []
        df_in = pd.DataFrame(rows)
        processed_df = self._transform_raw_to_model_df(df_in)
        preds = self.model.predict(processed_df)
        return [round(float(p), 2) for p in preds]


model_service = CalorieModelService()
