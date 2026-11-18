# ML Source & Dataset Backup (`D:\V3`)

This folder contains a read-only backup of your original ML scripts, preprocessing artifacts, evaluation metadata, and 70,000-row datasets from `D:\V3`:

- `predict.py`, `prepro.py`, `train.py`, `Rebuild.py`
- `preprocessed_workout_dataset.csv` (7.7 MB, 70,000 rows)
- `workout_dataset_70000_rebuilt.xlsx` (4.8 MB) & `workout_dataset_70000_rows.xlsx` (4.1 MB)
- `trained_models/preprocessor.pkl`, `trained_models/model_features.pkl`, `trained_models/feature_info.pkl`

## Note on `calorie_prediction_model.pkl` (2.93 GB)
GitHub enforces a strict **100 MB maximum file size limit** per file, so the `2.93 GB` trained binary `D:\V3\trained_models\calorie_prediction_model.pkl` cannot be uploaded directly to GitHub.

**How to back up or restore `calorie_prediction_model.pkl`:**
1. **Cloud / Drive Backup:** Copy `D:\V3\trained_models\calorie_prediction_model.pkl` to Google Drive, OneDrive, Hugging Face Hub, or an external drive.
2. **Exact Reproduction from This Repo:** Because `train.py` (with `random_state=42`) and `preprocessed_workout_dataset.csv` are backed up right here, running `python train.py` inside `ml_source_v3/` regenerates the identical model artifact.
