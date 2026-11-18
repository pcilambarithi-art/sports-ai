FROM python:3.14-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ /app/
COPY ml_source_v3/trained_models/ /models/
COPY ml_source_v3/preprocessed_workout_dataset.csv /dataset/preprocessed_workout_dataset.csv

ENV MODEL_DIR=/models \
    DATASET_PATH=/dataset/preprocessed_workout_dataset.csv \
    UPLOAD_DIR=/tmp/uploads \
    DATABASE_URL=sqlite:////tmp/sports_coaching.db \
    CORS_ORIGINS=https://pcilambarithi-art.github.io,http://localhost:5173

EXPOSE 7860

CMD ["sh", "-c", "if [ -n \"$MODEL_DOWNLOAD_URL\" ] && [ ! -f /models/calorie_prediction_model.pkl ]; then echo 'Downloading trained model...' && curl -L \"$MODEL_DOWNLOAD_URL\" -o /models/calorie_prediction_model.pkl; fi && alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 7860 --workers 1"]
