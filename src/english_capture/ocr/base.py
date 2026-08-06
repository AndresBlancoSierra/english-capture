from abc import ABC, abstractmethod
from pathlib import Path


class OCREngine(ABC):
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def recognize(self, image_path: Path) -> str:
        ...
