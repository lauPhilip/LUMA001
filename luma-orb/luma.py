# luma.py
import time
from dataclasses import dataclass


@dataclass
class LumaConfig:
    width: int = 800
    height: int = 480
    radius: int = 120            # FIXED orb radius
    attentive_seconds: float = 0.7


class Luma:
    def __init__(self, cfg: LumaConfig):
        self.cfg = cfg
        self._last_input_time = 0.0
        self.last_input_text = ""

    def receive_input(self, text: str = "") -> None:
        self._last_input_time = time.time()
        self.last_input_text = text.strip()

    def is_attentive(self, now: float | None = None) -> bool:
        now = time.time() if now is None else now
        return (now - self._last_input_time) <= self.cfg.attentive_seconds
