from .base import OCREngine
from .tesseract import TesseractEngine


def get_engine(name: str = "tesseract", **kwargs) -> OCREngine:
    engines = {
        "tesseract": TesseractEngine,
    }
    cls = engines.get(name)
    if cls is None:
        raise ValueError(f"Unknown OCR engine: {name}. Available: {list(engines.keys())}")
    return cls(**kwargs)
