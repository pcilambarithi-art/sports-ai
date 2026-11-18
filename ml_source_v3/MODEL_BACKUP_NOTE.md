# ML Source & Dataset Backup (`D:\V3`)

This folder contains a read-only backup of your original ML scripts, preprocessing artifacts, evaluation metadata, and 70,000-row datasets from `D:\V3`:

- `predict.py`, `prepro.py`, `train.py`, `Rebuild.py`
- `preprocessed_workout_dataset.csv` (7.7 MB, 70,000 rows)
- `workout_dataset_70000_rebuilt.xlsx` (4.8 MB) & `workout_dataset_70000_rows.xlsx` (4.1 MB)
- `trained_models/preprocessor.pkl`, `trained_models/model_features.pkl`, `trained_models/feature_info.pkl`

## Cloud Backup of `calorie_prediction_model.pkl` (2.93 GB)
Because GitHub enforces a strict **100 MB per-file limit**, your existing `2.93 GB` trained `ExtraTreesRegressor` binary has been uploaded and verified **100% backed up on Hugging Face Hub**:

- **Hugging Face Model Repository:** https://huggingface.co/ilambarithi/apexpulse-calorie-model
- **Direct Download URL:** `https://huggingface.co/ilambarithi/apexpulse-calorie-model/resolve/main/calorie_prediction_model.pkl`

You can also reproduce it identically anytime locally from this repository by running `python train.py` inside `ml_source_v3/` (`random_state=42`).
