# holo_orb.py
import math
import random
from dataclasses import dataclass


@dataclass
class HoloOrbStyle:
    points: int = 220
    links: int = 320
    sparks: int = 90
    rings: int = 6
    shell_layers: int = 4
    jitter: float = 0.012


class HoloOrb:
    def __init__(self, style: HoloOrbStyle | None = None, seed: int = 7):
        self.style = style or HoloOrbStyle()
        rnd = random.Random(seed)

        # Sphere points (Fibonacci sphere)
        self._pts = []
        n = self.style.points
        for i in range(n):
            y = 1 - (2 * i) / (n - 1)
            r = math.sqrt(max(0.0, 1 - y * y))
            phi = i * (math.pi * (3 - math.sqrt(5)))
            x = math.cos(phi) * r
            z = math.sin(phi) * r
            self._pts.append((x, y, z))

        # Stable random links
        self._links = [
            (rnd.randrange(n), rnd.randrange(n))
            for _ in range(self.style.links)
        ]

        # Sparks
        self._sparks = [
            (
                rnd.random() * 2 * math.pi,
                0.25 + rnd.random() * 1.1,
                rnd.random(),
                0.35 + rnd.random() * 0.65,
            )
            for _ in range(self.style.sparks)
        ]

        # Rings
        self._rings = [
            (rnd.choice(["x", "y", "z"]), rnd.random() * 2 * math.pi, 0.25 + rnd.random() * 0.9)
            for _ in range(self.style.rings)
        ]

    @staticmethod
    def _clamp(v: float) -> int:
        return max(0, min(255, int(v)))

    @classmethod
    def _rgba(cls, rgb: tuple[int, int, int], a: int) -> tuple[int, int, int, int]:
        r, g, b = rgb
        return (cls._clamp(r), cls._clamp(g), cls._clamp(b), cls._clamp(a))

    @staticmethod
    def _mul_color(rgb: tuple[int, int, int], m: float) -> tuple[int, int, int]:
        return (rgb[0] * m, rgb[1] * m, rgb[2] * m)

    def draw(self, screen, center_xy, radius, t, base_rgb):
        import pygame

        cx, cy = center_xy
        surf_size = radius * 2 + 140
        orb = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
        ox = oy = surf_size // 2

        # Outer glow
        for i in range(self.style.shell_layers):
            k = 1.0 - i / max(1, self.style.shell_layers)
            glow_r = int(radius * (1.05 + 0.22 * (i + 1)))
            col = self._rgba(self._mul_color(base_rgb, 0.55 + 0.25 * k), 40 * k)
            pygame.draw.circle(orb, col, (ox, oy), glow_r)

        # Rotation
        ax, ay, az = t * 0.55, t * 0.78, t * 0.36
        sx, cxr = math.sin(ax), math.cos(ax)
        sy, cyr = math.sin(ay), math.cos(ay)
        sz, czr = math.sin(az), math.cos(az)

        def rot(p):
            x, y, z = p
            j = self.style.jitter
            x += math.sin(t * 3.1 + x * 9) * j
            y += math.sin(t * 2.7 + y * 7) * j
            z += math.sin(t * 2.9 + z * 8) * j
            y, z = y * cxr - z * sx, y * sx + z * cxr
            x, z = x * cyr + z * sy, -x * sy + z * cyr
            x, y = x * czr - y * sz, x * sz + y * czr
            return x, y, z

        proj = []
        for p in self._pts:
            x, y, z = rot(p)
            depth = 2.6 + z
            px = ox + (x / depth) * radius * 1.55
            py = oy + (y / depth) * radius * 1.55
            proj.append((px, py, z))

        # Links
        for a, b in self._links:
            axp, ayp, azp = proj[a]
            bxp, byp, bzp = proj[b]
            if abs(azp - bzp) > 1.2:
                continue
            near = (azp + bzp + 2) / 4
            col = self._rgba(self._mul_color(base_rgb, 0.55 + 0.45 * near), 20 + 65 * near)
            pygame.draw.aaline(orb, col, (axp, ayp), (bxp, byp))

        # Nodes
        for px, py, z in proj:
            near = (z + 1) / 2
            size = 1 + int(2 * near)
            col = self._rgba(self._mul_color(base_rgb, 0.75 + 0.35 * near), 40 + 140 * near)
            orb.fill(col, (int(px) - size, int(py) - size, size * 2, size * 2))

        # Sparks
        for ang0, spd, ph, rf in self._sparks:
            ang = ang0 + t * spd
            rr = radius * (0.35 + 0.85 * rf)
            x = ox + math.cos(ang) * rr
            y = oy + math.sin(ang) * rr
            col = self._rgba(self._mul_color(base_rgb, 0.95), 80 + 140 * abs(math.sin(t * 6 + ph)))
            orb.fill(col, (int(x), int(y), 2, 2))

        # Core
        core_col = self._rgba(self._mul_color(base_rgb, 0.9), 110)
        pygame.draw.circle(orb, core_col, (ox, oy), int(radius * 0.35))

        screen.blit(orb, (cx - ox, cy - oy))
