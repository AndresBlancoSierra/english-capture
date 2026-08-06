import subprocess
import tempfile
from pathlib import Path

from PIL import Image

from .base import OCREngine


class TesseractEngine(OCREngine):
    def __init__(self, tesseract_cmd: str = "tesseract", lang: str = "eng"):
        self._tesseract_cmd = tesseract_cmd
        self._lang = lang

    @property
    def name(self) -> str:
        return f"tesseract ({self._lang})"

    def recognize(self, image_path: Path) -> str:
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            img = Image.open(image_path)
            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")
            img.save(tmp_path.replace(".txt", ".png"), "PNG")

            result = subprocess.run(
                [self._tesseract_cmd, tmp_path.replace(".txt", ".png"), tmp_path.replace(".txt", ""), "-l", self._lang, "--psm", "6"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            out_file = Path(tmp_path.replace(".txt", ".txt"))
            if out_file.exists():
                text = out_file.read_text().strip()
            else:
                text = result.stdout.strip()

            Path(tmp_path.replace(".txt", ".png")).unlink(missing_ok=True)
            Path(tmp_path).unlink(missing_ok=True)
            return text
        except subprocess.TimeoutExpired:
            Path(tmp_path.replace(".txt", ".png")).unlink(missing_ok=True)
            Path(tmp_path).unlink(missing_ok=True)
            raise TimeoutError("Tesseract timed out after 30s")
        except Exception:
            Path(tmp_path.replace(".txt", ".png")).unlink(missing_ok=True)
            Path(tmp_path).unlink(missing_ok=True)
            raise
