# Alp Ünlü tarafından yapılmıştır — @alppunlu
from __future__ import annotations

import json
import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

# EXE (PyInstaller one-file) icinde calisirken __file__ gecici bir klasoru
# gosterebilir. API anahtarinin her acilista korunmasi icin kullaniciya ait
# kalici AppData klasorunu kullan. Kaynak koddan calisirken de ayni konum
# kullanilir; boylece EXE ve kaynak surum ayni ayarlari gorur.
APPDATA_DIR = Path(os.environ.get("APPDATA", Path.home())) / "JARVIS"
CONFIG_DIR = APPDATA_DIR
CONFIG_PATH = CONFIG_DIR / "api_keys.json"


DEFAULT_CONFIG = {
    "gemini_api_key": "",
    "voice": "Charon",
    "youtube_api_key": "",
    "youtube_channel_handle": "",
}


def load_app_config() -> dict:
    config = dict(DEFAULT_CONFIG)
    try:
        raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            config.update(raw)
    except Exception:
        pass
    return config


def save_app_config(updates: dict) -> dict:
    config = load_app_config()
    for key, value in (updates or {}).items():
        if value is None:
            continue
        config[key] = value
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(
        json.dumps(config, indent=4, ensure_ascii=False),
        encoding="utf-8",
    )
    return config


def get_app_config_value(key: str, default=None):
    return load_app_config().get(key, default)


def has_gemini_api_key() -> bool:
    value = str(get_app_config_value("gemini_api_key", "") or "").strip()
    return bool(value)
