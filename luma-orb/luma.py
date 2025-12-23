# luma.py
import math
import time
from dataclasses import dataclass


@dataclass
class LumaConfig:
    width: int = 800
    height: int = 480

    # Visual sizing
    base_radius: int = 56          # base orb radius (used by renderer)
    pulse_amp: float = 0.10        # 10% breathing amplitude
    pulse_hz: float = 0.18         # breathing speed (0.12–0.25 feels natural)
    organic_wobble: float = 0.035  # adds irregularity (0.02–0.06)

    attentive_seconds: float = 0.7 # how long Luma stays green after input


class Luma:
    """
    Luma (character-like orb):
    - Stationary position (centered)
    - Organic breathing (radius modulation)
    - Turns green briefly on input
    """

    def __init__(self, cfg: LumaConfig):
        self.cfg = cfg
        self.x = cfg.width // 2
        self.y = cfg.height // 2

        self._last_input_time = 0.0
        self.last_input_text = ""

        # time anchor for smooth animation
        self._t0 = time.time()

    def receive_input(self, text: str = "") -> None:
        self._last_input_time = time.time()
        self.last_input_text = text.strip()

    def is_attentive(self, now: float | None = None) -> bool:
        if now is None:
            now = time.time()
        return (now - self._last_input_time) <= self.cfg.attentive_seconds

    def _smooth_noise(self, t: float) -> float:
        """
        Lightweight pseudo-noise using summed sines.
        Produces organic variation without extra dependencies.
        Output roughly in [-1, 1].
        """
        return (
            0.55 * math.sin(t * 1.13 + 0.7) +
            0.30 * math.sin(t * 2.37 + 2.1) +
            0.15 * math.sin(t * 3.91 + 4.0)
        )

    def radius_at(self, now: float | None = None) -> int:
        """
        Current orb radius (breathing + organic irregularity).
        """
        if now is None:
            now = time.time()

        t = now - self._t0

        # Base breathing
        breath = math.sin(2 * math.pi * self.cfg.pulse_hz * t)

        # Organic irregularity
        wobble = self._smooth_noise(t)

        # Attention “pulse” when input is received (subtle, not flashy)
        att = 0.0
        if self.is_attentive(now):
            # quick ease-out bump
            age = now - self._last_input_time
            att = math.exp(-age * 3.5) * 0.06  # 6% bump decays quickly

        scale = 1.0
        scale += self.cfg.pulse_amp * breath
        scale += self.cfg.organic_wobble * wobble
        scale += att

        # clamp to avoid extreme size changes
        scale = max(0.82, min(1.22, scale))

        return int(self.cfg.base_radius * scale)

    def update(self, dt: float) -> None:
        """
        Luma is stationary. This is here for API consistency.
        """
        return
