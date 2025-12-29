# energy_orb.py
import math
import random
from dataclasses import dataclass


@dataclass
class EnergyOrbStyle:
    res: int = 240
    filaments: int = 28
    sparks: int = 16
    rim_strength: float = 1.0


class EnergyOrb:
    def __init__(self, style: EnergyOrbStyle | None = None, seed: int = 7):
        self.style = style or EnergyOrbStyle()
        rnd = random.Random(seed)

        self._filaments = []
        for _ in range(self.style.filaments):
            self._filaments.append({
                "phase": rnd.random() * 2 * math.pi,
                "speed": 0.6 + rnd.random() * 1.2,
                "radius": 0.25 + rnd.random() * 0.55,
                "amp": 0.12 + rnd.random() * 0.22,
            })

        self._sparks = [rnd.random() * 2 * math.pi for _ in range(self.style.sparks)]

    def draw(self, screen, center, radius, t):
        import pygame

        n = self.style.res
        surf = pygame.Surface((n, n), pygame.SRCALPHA)
        cx = cy = n // 2
        R = n // 2

        # --- Base plasma (dark blue)
        for r in range(R, 0, -2):
            a = int(12 * (r / R))
            pygame.draw.circle(surf, (20, 60, 120, a), (cx, cy), r)

        # --- Electric filaments
        for f in self._filaments:
            pts = []
            ang0 = f["phase"] + t * f["speed"]
            for i in range(18):
                th = ang0 + i * 0.35
                rr = f["radius"] * R * (0.85 + 0.25 * math.sin(t * 1.8 + i))
                wob = f["amp"] * R * math.sin(th * 3.2 + t * 2.2)
                x = cx + math.cos(th) * rr + math.cos(th * 1.5) * wob
                y = cy + math.sin(th) * rr + math.sin(th * 1.3) * wob
                pts.append((x, y))

            col = (80, 180, 255, 80)
            if len(pts) > 1:
                pygame.draw.lines(surf, col, False, pts, 1)

        # --- Core sparks
        for ph in self._sparks:
            ang = ph + t * 2.4
            rr = R * 0.18
            x = cx + math.cos(ang) * rr
            y = cy + math.sin(ang) * rr
            pygame.draw.circle(surf, (160, 220, 255, 120), (int(x), int(y)), 2)

        # --- Hot rim (key visual)
        for i in range(3):
            a = int((90 - i * 25) * self.style.rim_strength)
            pygame.draw.circle(
                surf,
                (120, 220, 255, a),
                (cx, cy),
                R - i,
                2
            )

        # --- Clip to circle (hard)
        mask = pygame.Surface((n, n), pygame.SRCALPHA)
        pygame.draw.circle(mask, (255, 255, 255, 255), (cx, cy), R)
        surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        # --- Scale + draw
        orb = pygame.transform.smoothscale(surf, (radius * 2, radius * 2))
        screen.blit(orb, (center[0] - radius, center[1] - radius))
