r"""
One-command deployment script for Hugging Face Spaces (Free 16 GB RAM Docker tier).

Usage (PowerShell):
    $env:HF_TOKEN = "hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    cd D:\sports-coaching-system\backend
    .\.venv\Scripts\python.exe ..\deploy\huggingface\deploy-hf-space.py
"""

from __future__ import annotations

import os
import secrets
import shutil
import tempfile
from pathlib import Path

from huggingface_hub import HfApi

REPO_ROOT = Path(r"D:\sports-coaching-system")
MODEL_BIN_PATH = Path(r"D:\V3\trained_models\calorie_prediction_model.pkl")


def main() -> None:
    token = (os.getenv("HF_TOKEN") or "").strip()
    if not token or token == "hf_YOUR_WRITE_TOKEN" or not token.startswith("hf_"):
        print("\n[!] Please set your REAL Hugging Face Write token first:")
        print("    1. Sign in at https://huggingface.co/settings/tokens")
        print("    2. Click '+ Create new token' -> select 'Write' -> copy the token (starts with hf_...)")
        print('    3. Run: $env:HF_TOKEN = "hf_paste_your_real_token_here"')
        print(r"    4. Re-run: .\.venv\Scripts\python.exe ..\deploy\huggingface\deploy-hf-space.py")
        raise SystemExit(1)
    api = HfApi(token=token)
    me = api.whoami()
    username = me["name"]
    print(f"Authenticated on Hugging Face as: {username}")

    model_repo = f"{username}/apexpulse-calorie-model"
    space_repo = f"{username}/sports-ai-api"

    # 1. Upload existing 2.93 GB trained model to free HF Model Repo (read-only copy)
    print(f"\n[1/4] Creating/verifying model repo: {model_repo} ...")
    api.create_repo(repo_id=model_repo, repo_type="model", exist_ok=True, private=False)
    if MODEL_BIN_PATH.exists():
        print(f"Uploading {MODEL_BIN_PATH} (2.93 GB) -> {model_repo} ...")
        api.upload_file(
            path_or_fileobj=str(MODEL_BIN_PATH),
            path_in_repo="calorie_prediction_model.pkl",
            repo_id=model_repo,
            repo_type="model",
            commit_message="Upload existing trained ExtraTreesRegressor calorie model",
        )
    else:
        raise FileNotFoundError(f"Trained model not found at {MODEL_BIN_PATH}")

    model_download_url = f"https://huggingface.co/{model_repo}/resolve/main/calorie_prediction_model.pkl"

    # 2. Create free 16 GB RAM Docker Space
    print(f"\n[2/4] Creating/verifying free 16 GB Docker Space: {space_repo} ...")
    api.create_repo(
        repo_id=space_repo,
        repo_type="space",
        space_sdk="docker",
        space_hardware="cpu-basic",
        exist_ok=True,
        private=False,
    )

    # 3. Stage clean Space upload directory (excludes .venv, *.db, .env, uploads)
    print("\n[3/4] Packaging backend + ml_source_v3 + Dockerfile ...")
    with tempfile.TemporaryDirectory() as tmp:
        stage = Path(tmp) / "space"
        stage.mkdir(parents=True, exist_ok=True)

        shutil.copy2(REPO_ROOT / "deploy" / "huggingface" / "Dockerfile", stage / "Dockerfile")
        shutil.copy2(REPO_ROOT / "deploy" / "huggingface" / "README_HF_SPACE.md", stage / "README.md")

        def _ignore(_dir, names):
            ignored = {".venv", "__pycache__", ".pytest_cache", "uploads", ".env", "trained_coaching_ai"}
            return [n for n in names if n in ignored or n.endswith(".db") or n.endswith(".pyc")]

        shutil.copytree(REPO_ROOT / "backend", stage / "backend", ignore=_ignore)
        shutil.copytree(REPO_ROOT / "ml_source_v3", stage / "ml_source_v3")

        api.upload_folder(
            folder_path=str(stage),
            repo_id=space_repo,
            repo_type="space",
            commit_message="Deploy ApexPulse AI Sports Coaching FastAPI backend",
        )

    # 4. Configure Space Variables & Secrets
    print("\n[4/4] Setting Space environment variables & secrets ...")
    api.add_space_variable(repo_id=space_repo, key="MODEL_DOWNLOAD_URL", value=model_download_url)
    api.add_space_variable(
        repo_id=space_repo,
        key="CORS_ORIGINS",
        value="https://pcilambarithi-art.github.io,http://localhost:5173",
    )
    api.add_space_secret(repo_id=space_repo, key="SECRET_KEY", value=secrets.token_hex(32))
    api.add_space_secret(repo_id=space_repo, key="SENSOR_API_KEY", value=secrets.token_hex(24))

    space_url = f"https://{username.lower().replace('_', '-')}-sports-ai-api.hf.space"
    print("\n" + "=" * 68)
    print("HUGGING FACE SPACE DEPLOYED!")
    print(f"Permanent Always-On Backend URL : {space_url}")
    print(f"Space Build Logs                : https://huggingface.co/spaces/{space_repo}")
    print("Next step: Set GitHub Actions Variable VITE_API_BASE_URL to the URL above")
    print("           and re-run 'Deploy Frontend to GitHub Pages'.")
    print("=" * 68)


if __name__ == "__main__":
    main()
