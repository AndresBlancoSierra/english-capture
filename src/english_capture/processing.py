import sys
from pathlib import Path

from .config import load_config, ensure_dirs, DB_PATH
from . import database as db
from .ocr import get_engine
from .storage import get_image_path


def process_all_pending():
    cfg = load_config()
    conn = db.get_conn(DB_PATH)
    engine = get_engine(cfg["ocr_engine"], tesseract_cmd=cfg["tesseract_cmd"], lang=cfg["tesseract_lang"])
    pending = db.get_pending_captures(conn)
    if not pending:
        conn.close()
        return 0
    for cap in pending:
        try:
            img_path = get_image_path(cap["image_path"])
            if not img_path.exists():
                db.mark_failed(conn, cap["id"], f"Image not found: {img_path}")
                continue
            text = engine.recognize(img_path)
            db.mark_processed(conn, cap["id"], text, engine.name)
        except Exception as e:
            db.mark_failed(conn, cap["id"], str(e))
    conn.close()
    return len(pending)


def process_one(capture_id: str) -> str | None:
    cfg = load_config()
    conn = db.get_conn(DB_PATH)
    engine = get_engine(cfg["ocr_engine"], tesseract_cmd=cfg["tesseract_cmd"], lang=cfg["tesseract_lang"])
    cap = db.get_capture(conn, capture_id)
    if not cap:
        conn.close()
        return None
    try:
        img_path = get_image_path(cap["image_path"])
        if not img_path.exists():
            db.mark_failed(conn, cap["id"], f"Image not found: {img_path}")
            conn.close()
            return None
        text = engine.recognize(img_path)
        db.mark_processed(conn, cap["id"], text, engine.name)
        conn.close()
        return text
    except Exception as e:
        db.mark_failed(conn, cap["id"], str(e))
        conn.close()
        return None
