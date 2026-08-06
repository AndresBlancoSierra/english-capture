import json
import os
from pathlib import Path

XDG_DATA_HOME = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
XDG_CONFIG_HOME = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
XDG_PICTURES_DIR = Path(os.environ.get("XDG_PICTURES_DIR", Path.home() / "Pictures"))

DATA_DIR = XDG_DATA_HOME / "english-capture"
CONFIG_DIR = XDG_CONFIG_HOME / "english-capture"
CONFIG_FILE = CONFIG_DIR / "config.json"
SCREENSHOT_DIR = XDG_PICTURES_DIR / "english-capture"

INBOX_DIR = DATA_DIR / "inbox"
PROCESSED_DIR = DATA_DIR / "processed"
FAILED_DIR = DATA_DIR / "failed"
DB_PATH = DATA_DIR / "database" / "captures.db"

DIRS = [INBOX_DIR, PROCESSED_DIR, FAILED_DIR, DATA_DIR / "database"]

DEFAULT_CONFIG = {
    "ocr_engine": "tesseract",
    "tesseract_lang": "eng",
    "tesseract_cmd": "tesseract",
    "screenshot_tool": "grim",
    "selection_tool": "slurp",
    "context_region_scale": 2.0,
    "save_context_screenshot": False,
    "notifications_enabled": True,
    "auto_process_on_capture": True,
}


def ensure_dirs():
    for d in DIRS:
        d.mkdir(parents=True, exist_ok=True)


def load_config():
    if not CONFIG_FILE.exists():
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(json.dumps(DEFAULT_CONFIG, indent=2))
        return dict(DEFAULT_CONFIG)
    return {**DEFAULT_CONFIG, **json.loads(CONFIG_FILE.read_text())}


def save_config(cfg):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))
