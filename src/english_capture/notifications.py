import subprocess

from .config import load_config


def _notify(summary: str, body: str = "", urgency: str = "normal", icon: str = ""):
    cfg = load_config()
    if not cfg.get("notifications_enabled", True):
        return
    cmd = ["notify-send", "-u", urgency, summary]
    if body:
        cmd.append(body)
    if icon:
        cmd.extend(["-i", icon])
    subprocess.run(cmd, capture_output=True, timeout=5)


def notify_captured(image_path: str = ""):
    _notify("Captura guardada", "", "normal", image_path)


def notify_ocr_done(text: str):
    _notify("OCR completado", f"\"{text[:80]}\"" if text else "(texto vacío)")


def notify_error(msg: str):
    _notify("Error en captura", msg, "critical")
