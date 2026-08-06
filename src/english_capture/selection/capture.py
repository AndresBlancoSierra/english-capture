import subprocess

from ..config import ensure_dirs, DB_PATH
from .. import database as db
from ..storage import save_screenshot
from ..notifications import notify_captured, notify_ocr_done, notify_error
from ..processing import process_one


def capture_from_geometry(x1, y1, x2, y2):
    rx1 = min(x1, x2)
    ry1 = min(y1, y2)
    rw = abs(x2 - x1)
    rh = abs(y2 - y1)

    if rw < 10 or rh < 10:
        return

    ensure_dirs()
    db.init_db(DB_PATH)

    geometry = f"{rx1},{ry1} {rw}x{rh}"

    result = subprocess.run(
        ["grim", "-g", geometry, "-"],
        capture_output=True,
        timeout=10,
    )
    if result.returncode != 0:
        return

    image_path = save_screenshot(result.stdout)

    conn = db.get_conn(DB_PATH)
    cap_id = db.insert_capture(conn, str(image_path), None, geometry)
    conn.close()

    notify_captured(str(image_path))

    text = process_one(cap_id)
    if text is not None:
        notify_ocr_done(text)
    else:
        notify_error("OCR falló en la captura")
