---
title: ApexPulse AI Sports Coaching Backend
emoji: 🏆
colorFrom: purple
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# ApexPulse AI Sports Coaching Backend (Hugging Face Docker Space — Free 16 GB RAM)

This Docker Space runs the real **FastAPI + SQLAlchemy + OpenCV + Companion AI + Your Existing `ExtraTreesRegressor` Model** on a **permanent HTTPS URL** (`https://<your-hf-username>-sports-ai-api.hf.space`) that **automatically wakes up whenever someone opens your GitHub Pages website** (`https://pcilambarithi-art.github.io/sports-ai/`).

## 3-Minute Free Always-On Setup
1. Create a free account at https://huggingface.co and click **New Space** → name it `sports-ai-api` → select **Docker (Blank)** → **Free CPU Basic (2 vCPU, 16 GB RAM)**.
2. Upload your `D:\V3\trained_models\calorie_prediction_model.pkl` (2.93 GB) to a free Hugging Face Model Repo (e.g. `<your-hf-username>/apexpulse-calorie-model`).
3. Copy this repo's `backend/` + `ml_source_v3/` + `deploy/huggingface/Dockerfile` into the Space, and set Space Secret/Variables:
   - `MODEL_DOWNLOAD_URL=https://huggingface.co/<your-hf-username>/apexpulse-calorie-model/resolve/main/calorie_prediction_model.pkl`
   - `SECRET_KEY=<random-32-char-secret>`
   - `CORS_ORIGINS=https://pcilambarithi-art.github.io`
4. Copy your permanent Space URL (`https://<your-hf-username>-sports-ai-api.hf.space`) into GitHub repo **Settings → Secrets and variables → Actions → Variables → `VITE_API_BASE_URL`**, and re-run the GitHub Pages build once!
