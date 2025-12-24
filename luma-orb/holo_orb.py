# holo_orb.py
import math
import random
from dataclasses import dataclass


@dataclass
class HoloOrbStyle:
    points: int = 240
    links: int = 360
    sparks: int = 120
    rings: int = 7
    shell_layers: int = 5
    jitter: float = 0.014

    # New: center softness (prevents “core disk” look)
    center_hole: float = 0.22   # 0.15–0.35 (higher = more hollow center)
    center_fade: float = 0.18   # 0.10–0.30 (how smoothly it ramps up)


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
        self._links = []
        for _ in range(self.style.links):
            a = rnd.randrange(n)
            b = rnd.randrange(n)
            if a != b:
                self._links.append((a, b))

        # Sparks
        self._sparks = [
            (
                rnd.random() * 2 * math.pi,
                0.25 + rnd.random() * 1.25,
                rnd.random(),
                0.25 + rnd.random() * 0.8,
            )
            for _ in range(self.style.sparks)
        ]

        # Rings
        self._rings = [
            (rnd.choice(["x", "y", "z"]), rnd.random() * 2 * math.pi, 0.25 + rnd.random() * 0.9)
            for _ in range(self.style.rings)
        ]

    @staticmethod
    def _clamp_byte(v: float) -> int:
        return max(0, min(255, int(v)))

    @classmethod
    def _rgba(cls, rgb: tuple[float, float, float], a: float) -> tuple[int, int, int, int]:
        r, g, b = rgb
        return (cls._clamp_byte(r), cls._clamp_byte(g), cls._clamp_byte(b), cls._clamp_byte(a))

    @staticmethod
    def _mul(rgb: tuple[int, int, int], m: float) -> tuple[float, float, float]:
        return (rgb[0] * m, rgb[1] * m, rgb[2] * m)

    @staticmethod
    def _smoothstep(edge0: float, edge1: float, x: float) -> float:
        # smooth 0..1 ramp
        if edge0 == edge1:
            return 1.0 if x >= edge1 else 0.0
        t = (x - edge0) / (edge1 - edge0)
        t = 0.0 if t < 0.0 else 1.0 if t > 1.0 else t
        return t * t * (3.0 - 2.0 * t)

    def draw(self, screen, center_xy: tuple[int, int], radius: int, t: float, base_rgb: tuple[int, int, int]) -> None:
        import pygame

        cx, cy = center_xy

        surf_size = radius * 2 + 160
        orb = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
        ox = oy = surf_size // 2

        # Outer glow shell (soft and volumetric)
        for i in range(self.style.shell_layers):
            k = 1.0 - i / max(1, self.style.shell_layers)
            glow_r = int(radius * (1.15 + 0.26 * (i + 1)))
            alpha = 18 + 40 * k
            col = self._rgba(self._mul(base_rgb, 0.42 + 0.20 * k), alpha)
            pygame.draw.circle(orb, col, (ox, oy), glow_r)

        # Rotation angles
        ax = t * 0.55
        ay = t * 0.78
        az = t * 0.36

        sx, cxr = math.sin(ax), math.cos(ax)
        sy, cyr = math.sin(ay), math.cos(ay)
        sz, czr = math.sin(az), math.cos(az)

        def rot(p):
            x, y, z = p
            j = self.style.jitter
            x += math.sin(t * 3.1 + x * 9.0) * j
            y += math.sin(t * 2.7 + y * 7.0) * j
            z += math.sin(t * 2.9 + z * 8.0) * j

            # rotate around x
            y, z = (y * cxr - z * sx), (y * sx + z * cxr)
            # rotate around y
            x, z = (x * cyr + z * sy), (-x * sy + z * cyr)
            # rotate around z
            x, y = (x * czr - y * sz), (x * sz + y * czr)
            return x, y, z

        # Project points
        proj = []
        for p in self._pts:
            x, y, z = rot(p)
            depth = 2.7 + z  # mild perspective
            px = ox + (x / depth) * radius * 1.60
            py = oy + (y / depth) * radius * 1.60

            # normalized radial distance from center in 2D projection (0..~1)
            dx = (px - ox) / (radius * 1.60)
            dy = (py - oy) / (radius * 1.60)
            r2d = math.sqrt(dx * dx + dy * dy)

            proj.append((px, py, z, r2d))

        # Radial alpha mask: keep center hollow/soft (prevents "core disk")
        hole = self.style.center_hole
        fade = self.style.center_fade
        def radial_gain(r2d: float) -> float:
            # 0 at center; ramps to 1 outside the hole boundary
            return self._smoothstep(hole, hole + fade, r2d)

        # Links (filaments)
        for a, b in self._links:
            axp, ayp, azp, ar = proj[a]
            bxp, byp, bzp, br = proj[b]
            if abs(azp - bzp) > 1.2:
                continue

            # depth-based intensity
            zavg = 0.5 * (azp + bzp)
            near = self._smoothstep(-1.0, 1.0, zavg)

            # radial suppression near center
            rg = 0.5 * (radial_gain(ar) + radial_gain(br))

            alpha = (10 + 85 * near) * rg
            if alpha < 2:
                continue

            col = self._rgba(self._mul(base_rgb, 0.55 + 0.55 * near), alpha)
            pygame.draw.aaline(orb, col, (axp, ayp), (bxp, byp))

        # Nodes (sparkle points)
        for px, py, z, r2d in proj:
            near = self._smoothstep(-1.0, 1.0, z)
            rg = radial_gain(r2d)

            # if in center region, mostly invisible
            alpha = (18 + 170 * near) * rg
            if alpha < 2:
                continue

            size = 1 + int(2 * near)
            col = self._rgba(self._mul(base_rgb, 0.68 + 0.42 * near), alpha)
            orb.fill(col, (int(px) - size, int(py) - size, size * 2, size * 2))

        # Rings / arcs (energy motion cues)
        for axis, phase, speed in self._rings:
            th = t * speed + phase
            ring_r = radius * (0.65 + 0.35 * (0.5 + 0.5 * math.sin(th * 0.7 + phase)))
            arc_rect = pygame.Rect(0, 0, int(ring_r * 2), int(ring_r * 2))
            arc_rect.center = (ox, oy)

            start = th
            end = th + (1.1 + 0.9 * math.sin(th * 0.9 + 2.0))
            alpha = 18 + 95 * (0.5 + 0.5 * math.sin(th))

            col = self._rgba(self._mul(base_rgb, 0.80), alpha)
            pygame.draw.arc(orb, col, arc_rect, start, end, 2)

        # Sparks (tiny moving particles, also suppressed near center)
        for ang0, spd, ph, rf in self._sparks:
            ang = ang0 + t * spd
            rr = radius * (0.40 + 0.80 * rf)
            x = ox + math.cos(ang) * rr
            y = oy + math.sin(ang) * rr * (0.60 + 0.40 * math.sin(ang * 1.3 + ph))

            # radial gain based on spark location
            dx = (x - ox) / (radius * 1.60)
            dy = (y - oy) / (radius * 1.60)
            rg = radial_gain(math.sqrt(dx * dx + dy * dy))

            tw = 0.5 + 0.5 * math.sin(t * 6.0 + ph * 12.0)
            alpha = (35 + 160 * tw) * rg
            if alpha < 2:
                continue

            col = self._rgba(self._mul(base_rgb, 0.95), alpha)
            orb.fill(col, (int(x), int(y), 2, 2))

        # IMPORTANT: No core circle. This is what removes the visible center disk.

        screen.blit(orb, (cx - ox, cy - oy))
