from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "ApexPulse AI Sports Coaching System"
    APP_ENV: str = "development"
    DEBUG: bool = False

    SECRET_KEY: str = "apexpulse-dev-secret-key-override-in-production-32bytes"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 720
    SENSOR_API_KEY: str = "apexpulse-sensor-key-local-dev"

    DATABASE_URL: str = "sqlite:///./sports_coaching.db"

    MODEL_DIR: str = r"D:\V3\trained_models"
    MODEL_FILE: str = "calorie_prediction_model.pkl"
    PREPROCESSOR_FILE: str = "preprocessor.pkl"
    MODEL_FEATURES_FILE: str = "model_features.pkl"
    FEATURE_INFO_FILE: str = "feature_info.pkl"
    DATASET_PATH: str = r"D:\V3\preprocessed_workout_dataset.csv"
    AUTO_LOAD_MODEL: bool = True

    UPLOAD_DIR: str = "uploads"
    MAX_VIDEO_SIZE_MB: int = 150

    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000"

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def model_path(self) -> Path:
        return Path(self.MODEL_DIR) / self.MODEL_FILE

    @property
    def preprocessor_path(self) -> Path:
        return Path(self.MODEL_DIR) / self.PREPROCESSOR_FILE

    @property
    def model_features_path(self) -> Path:
        return Path(self.MODEL_DIR) / self.MODEL_FEATURES_FILE

    @property
    def feature_info_path(self) -> Path:
        return Path(self.MODEL_DIR) / self.FEATURE_INFO_FILE

    @property
    def dataset_file_path(self) -> Path:
        return Path(self.DATASET_PATH)

    @property
    def upload_path(self) -> Path:
        p = Path(self.UPLOAD_DIR)
        p.mkdir(parents=True, exist_ok=True)
        return p


settings = Settings()
