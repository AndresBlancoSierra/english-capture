from datetime import datetime, timezone
from pathlib import Path

from .config import INBOX_DIR, PROCESSED_DIR, FAILED_DIR


def _timestamp():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")


def _short_id():
    import uuid

    return uuid.uuid4().hex[:8]


def save_screenshot(data: bytes, suffix: str = "") -> Path:
    ts = _timestamp()
    sid = _short_id()
    label = f"{ts}_{sid}"
    if suffix:
        label = f"{label}_{suffix}"
    dest = INBOX_DIR / f"{label}.png"
    dest.write_bytes(data)
    return dest


def move_to_processed(path: Path) -> Path:
    dest = PROCESSED_DIR / path.name
    path.rename(dest)
    return dest


def move_to_failed(path: Path) -> Path:
    dest = FAILED_DIR / path.name
    path.rename(dest)
    return dest


def get_image_path(path_str: str) -> Path:
    p = Path(path_str)
    if p.exists():
        return p
    for d in [INBOX_DIR, PROCESSED_DIR, FAILED_DIR]:
        candidate = d / p.name
        if candidate.exists():
            return candidate
    return p
