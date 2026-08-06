import subprocess
from pathlib import Path

from .config import load_config
from .storage import save_screenshot


def _get_selection(config: dict) -> str:
    slurp = config["selection_tool"]
    result = subprocess.run(
        [slurp],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        raise RuntimeError("Selection cancelled or failed")
    sel = result.stdout.strip()
    if not sel:
        raise RuntimeError("Empty selection")
    return sel


def capture_region() -> tuple[bytes, str]:
    cfg = load_config()
    selection = _get_selection(cfg)
    grim = cfg["screenshot_tool"]
    result = subprocess.run(
        [grim, "-g", selection, "-"],
        capture_output=True,
        timeout=10,
    )
    if result.returncode != 0:
        raise RuntimeError(f"grim failed: {result.stderr.decode().strip()}")
    return result.stdout, selection


def capture_context(selection: str) -> tuple[bytes, str] | None:
    cfg = load_config()
    scale = cfg.get("context_region_scale", 2.0)
    if not cfg.get("save_context_screenshot", False):
        return None
    parts = selection.replace(",", " ").replace("x", " ").split()
    x, y, w, h = map(int, parts)
    cx, cy = x + w // 2, y + h // 2
    cw, ch = int(w * scale), int(h * scale)
    cx2, cy2 = max(0, cx - cw // 2), max(0, cy - ch // 2)
    context_geo = f"{cx2},{cy2} {cw}x{ch}"
    grim = cfg["screenshot_tool"]
    result = subprocess.run(
        [grim, "-g", context_geo, "-"],
        capture_output=True,
        timeout=10,
    )
    if result.returncode != 0:
        return None
    return result.stdout, context_geo


def do_capture() -> tuple[Path, str, Path | None, str | None]:
    img_data, geometry = capture_region()
    image_path = save_screenshot(img_data)
    context_path = None
    context_geo = None
    ctx = capture_context(geometry)
    if ctx:
        ctx_data, context_geo = ctx
        context_path = save_screenshot(ctx_data, suffix="ctx")
    return image_path, geometry, context_path, context_geo
