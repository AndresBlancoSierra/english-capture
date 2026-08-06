import subprocess
import sys
from pathlib import Path

from . import database as db
from .config import ensure_dirs, load_config, CONFIG_DIR, DATA_DIR, DB_PATH, SCREENSHOT_DIR, DIRS
from .notifications import notify_captured, notify_ocr_done, notify_error
from .processing import process_all_pending, process_one
from .screenshot import do_capture


def cmd_capture():
    ensure_dirs()
    cfg = load_config()
    try:
        image_path, geometry, context_path, context_geo = do_capture()
    except RuntimeError as e:
        msg = str(e)
        notify_error(msg)
        print(f"Error: {msg}", file=sys.stderr)
        return 1
    conn = db.get_conn(DB_PATH)
    cap_id = db.insert_capture(
        conn,
        str(image_path),
        str(context_path) if context_path else None,
        geometry,
    )
    conn.close()
    notify_captured(str(image_path))
    print(f"Captured: {image_path.name}")
    print(f"ID: {cap_id}")
    if cfg.get("auto_process_on_capture", True):
        text = process_one(cap_id)
        if text is not None:
            notify_ocr_done(text)
            print(f"OCR: \"{text[:80]}\"" if text else "OCR: (empty)")
        else:
            notify_error("OCR failed")
            print("OCR: failed", file=sys.stderr)
    return 0


def cmd_process():
    ensure_dirs()
    count = process_all_pending()
    print(f"Processed {count} pending capture(s)" if count else "No pending captures")
    return 0


def cmd_list():
    conn = db.get_conn(DB_PATH)
    captures = db.list_captures(conn)
    conn.close()
    if not captures:
        print("No captures yet")
        return 0
    print(f"{'ID':<10} {'Fecha':<22} {'Estado':<12} Texto")
    print("-" * 80)
    for c in captures:
        date = c["created_at"][:19].replace("T", " ")
        text = (c["ocr_text"] or "")[:50].replace("\n", " ")
        status = c["status"]
        print(f"{c['id']:<10} {date:<22} {status:<12} {text}")
    return 0


def cmd_show(capture_id: str):
    conn = db.get_conn(DB_PATH)
    cap = db.get_capture(conn, capture_id)
    conn.close()
    if not cap:
        print(f"Capture '{capture_id}' not found", file=sys.stderr)
        return 1
    print(f"ID:             {cap['id']}")
    print(f"Created:        {cap['created_at']}")
    print(f"Status:         {cap['status']}")
    print(f"Image:          {cap['image_path']}")
    if cap.get("context_image_path"):
        print(f"Context:        {cap['context_image_path']}")
    if cap.get("selection_geometry"):
        print(f"Geometry:       {cap['selection_geometry']}")
    if cap.get("ocr_text"):
        print(f"OCR text:       {cap['ocr_text']}")
    if cap.get("ocr_engine"):
        print(f"OCR engine:     {cap['ocr_engine']}")
    if cap.get("processed_at"):
        print(f"Processed at:   {cap['processed_at']}")
    if cap.get("error"):
        print(f"Error:          {cap['error']}")
    if cap.get("retry_count"):
        print(f"Retries:        {cap['retry_count']}")

    img_path = Path(cap["image_path"])
    if img_path.exists():
        try:
            subprocess.run(["imv", str(img_path)], timeout=30)
        except FileNotFoundError:
            try:
                subprocess.run(["xdg-open", str(img_path)], timeout=30)
            except Exception:
                pass
        except Exception:
            pass
    return 0


def cmd_retry(capture_id: str):
    conn = db.get_conn(DB_PATH)
    cap = db.get_capture(conn, capture_id)
    if not cap:
        print(f"Capture '{capture_id}' not found", file=sys.stderr)
        conn.close()
        return 1
    db.mark_pending(conn, capture_id)
    conn.close()
    text = process_one(capture_id)
    if text is not None:
        notify_ocr_done(text)
        print(f"Retry successful: \"{text[:80]}\"" if text else "Retry: (empty text)")
        return 0
    else:
        notify_error(f"Retry failed for {capture_id}")
        print(f"Retry failed for {capture_id}", file=sys.stderr)
        return 1


def cmd_stats():
    conn = db.get_conn(DB_PATH)
    stats = db.get_stats(conn)
    conn.close()
    print(f"Total:     {stats['total']}")
    print(f"Pending:   {stats['pending']}")
    print(f"Processed: {stats['processed']}")
    print(f"Failed:    {stats['failed']}")
    return 0


def cmd_config():
    cfg = load_config()
    print(f"Config file:  {CONFIG_DIR / 'config.json'}")
    print(f"Data dir:     {DATA_DIR}")
    print(f"Screenshots:  {SCREENSHOT_DIR}")
    print(f"Database:     {DB_PATH}")
    print()
    for k, v in cfg.items():
        print(f"  {k}: {v}")
    return 0


def cmd_daemon():
    from .selection.daemon import main as daemon_main
    return daemon_main()


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print("Usage: english-capture <command> [args]")
        print()
        print("Commands:")
        print("  capture              Take a screenshot and run OCR")
        print("  process              Process all pending captures")
        print("  list                 List all captures")
        print("  show     <id>        Show capture details")
        print("  retry    <id>        Retry OCR on a capture")
        print("  stats                Show statistics")
        print("  config               Show configuration")
        print("  daemon               Start mouse selection daemon")
        return 0

    cmd = sys.argv[1]
    ensure_dirs()
    from .config import DB_PATH
    db.init_db(DB_PATH)

    match cmd:
        case "capture":
            return cmd_capture()
        case "process":
            return cmd_process()
        case "list":
            return cmd_list()
        case "show":
            if len(sys.argv) < 3:
                print("Usage: english-capture show <id>", file=sys.stderr)
                return 1
            return cmd_show(sys.argv[2])
        case "retry":
            if len(sys.argv) < 3:
                print("Usage: english-capture retry <id>", file=sys.stderr)
                return 1
            return cmd_retry(sys.argv[2])
        case "stats":
            return cmd_stats()
        case "config":
            return cmd_config()
        case "daemon":
            return cmd_daemon()
        case _:
            print(f"Unknown command: {cmd}", file=sys.stderr)
            return 1


if __name__ == "__main__":
    sys.exit(main())
