# smooth_orb.py
import math
from dataclasses import dataclass

import numpy as np


@dataclass
class SmoothOrbStyle:
    internal_res: int = 220       # 160–280
    blur_passes: int = 2          # 1–3 (higher = smoother, slower)
    vignette_strength: float = 0.50
    rim_strength: float = 0.35
    highlight_strength: float = 0.45


def _smoothstep(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3.0 - 2.0 * x)


class SmoothOrb:
    """
    Full-orb animated color field (fills the entire circle).
    Stationary orb; colors flow within.
    Uses numpy + pygame.surfarray for performance.
    """

    def __init__(self, style: SmoothOrbStyle | None = None):
        self.style = style or SmoothOrbStyle()
        self._mask_cache = {}

        # Precompute coordinate grid once
        n = self.style.internal_res
        y, x = np.mgrid[0:n, 0:n].astype(np.float32)
        cx = cy = (n - 1) / 2.0
        R = n / 2.0
        self._nx = (x - cx) / R
        self._ny = (y - cy) / R
        self._rr = np.sqrt(self._nx**2 + self._ny**2)

    def _palette(self, attentive: bool):
        # Use 3 anchors so the field has variety but stays coherent.
        if attentive:
            # Green/teal/lime family
            return np.array([
                [35, 230, 130],
                [40, 255, 185],
                [170, 255, 120],
            ], dtype=np.float32)
        else:
            # Blue/cyan/violet family
            return np.array([
                [60, 150, 255],
                [75, 245, 255],
                [170, 130, 255],
            ], dtype=np.float32)

    def _circle_alpha_mask(self, n: int):
        """
        Alpha mask (0 outside circle). Cached as uint8 [H,W].
        """
        if n in self._mask_cache:
            return self._mask_cache[n]

        rr = self._rr
        # soft edge
        edge = np.clip(1.0 - rr, 0.0, 1.0)
        a = (255.0 * (edge ** 0.60)).astype(np.uint8)
        a[rr > 1.0] = 0
        self._mask_cache[n] = a
        return a

    def _flow_field(self, t: float):
        """
        Continuous moving scalar field 0..1 that fills the orb.
        Built from several smooth sine layers (cheap "procedural fluid").
        """
        nx = self._nx
        ny = self._ny

        # Time-driven offsets create apparent “movement”
        tx = 0.25 * math.cos(t * 0.55)
        ty = 0.25 * math.sin(t * 0.48)

        # Multi-layer smooth waves (vector-ish flow)
        f1 = np.sin((nx * 3.2 + ny * 2.1 + tx) * 2.0 + t * 0.7)
        f2 = np.sin((nx * -2.3 + ny * 3.7 + ty) * 2.0 + t * 0.9)
        f3 = np.sin((nx * 5.1 + ny * -4.2 + tx * 0.7) * 1.6 + t * 0.55)

        # Combine and normalize
        v = (0.45 * f1 + 0.35 * f2 + 0.20 * f3)
        v = (v - v.min()) / (v.max() - v.min() + 1e-6)  # 0..1

        # Add a slow “roll” so it feels like it circulates
        roll = 0.5 + 0.5 * np.sin(t * 0.35 + (nx * 1.2 - ny * 1.0) * 2.0)
        v = 0.72 * v + 0.28 * roll

        return _smoothstep(v)

    def draw(self, screen, center_xy, radius: int, t: float, base_rgb, attentive: bool):
        import pygame
        import pygame.surfarray as surfarray

        n = self.style.internal_res
        field = self._flow_field(t)

        # Build 2 blend weights so we can blend among 3 palette anchors
        # w0 + w1 + w2 = 1, where w1 is the main moving field
        w1 = field
        w2 = _smoothstep(np.roll(field, shift=18, axis=1))
        w0 = 1.0 - np.clip(w1 * 0.65 + w2 * 0.35, 0.0, 1.0)

        pal = self._palette(attentive)  # shape (3,3)

        # RGB = weighted mix of palette anchors
        rgb = (w0[..., None] * pal[0] +
               w1[..., None] * pal[1] +
               w2[..., None] * pal[2])

        # Optional bias toward the requested base color (keeps identity consistent)
        base = np.array(base_rgb, dtype=np.float32)
        rgb = 0.78 * rgb + 0.22 * base

        # Vignette (alpha-only) to keep edges soft without greying colors
        rr = self._rr
        edge = np.clip(1.0 - rr, 0.0, 1.0)
        vign = (0.75 + 0.25 * (edge ** (0.8 + 1.0 * self.style.vignette_strength)))
        rgb = rgb * vign[..., None]

        # Clamp
        rgb = np.clip(rgb, 0, 255).astype(np.uint8)

        # Alpha mask (hard requirement: nothing outside)
        alpha = self._circle_alpha_mask(n)

        # Build surface
        surf = pygame.Surface((n, n), pygame.SRCALPHA)

        # surfarray expects (W,H,3) for pixels3d
        arr_rgb = surfarray.pixels3d(surf)
        arr_a = surfarray.pixels_alpha(surf)

        arr_rgb[:, :, :] = np.transpose(rgb, (1, 0, 2))    # (H,W,3) -> (W,H,3)
        arr_a[:, :] = np.transpose(alpha, (1, 0))          # (H,W)   -> (W,H)

        del arr_rgb, arr_a  # unlock surface

        # Blur (cheap down/up)
        blur = surf
        for _ in range(self.style.blur_passes):
            small = pygame.transform.smoothscale(blur, (max(2, n // 2), max(2, n // 2)))
            blur = pygame.transform.smoothscale(small, (n, n))

        # Inside-only rim + highlight (still clipped because blur already has alpha mask)
        overlay = pygame.Surface((n, n), pygame.SRCALPHA)
        Rpx = int(n * 0.5)

        rim_a = int(18 * self.style.rim_strength)
        pygame.draw.circle(overlay, (255, 255, 255, rim_a), (n // 2, n // 2), int(Rpx * 0.985), 2)

        hi_a = int(14 * self.style.highlight_strength)
        pygame.draw.circle(overlay, (255, 255, 255, hi_a), (int(n * 0.38), int(n * 0.32)), int(Rpx * 0.30), 0)

        blur.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

        # Re-apply circular alpha (ensures overlay never leaks)
        mask_alpha = self._circle_alpha_mask(n)
        arr_a2 = pygame.surfarray.pixels_alpha(blur)
        arr_a2[:, :] = np.minimum(arr_a2[:, :], np.transpose(mask_alpha, (1, 0)))
        del arr_a2

        # Scale to breathing radius and draw
        size = max(8, radius * 2)
        orb_img = pygame.transform.smoothscale(blur, (size, size))
        cx, cy = center_xy
        screen.blit(orb_img, (cx - size // 2, cy - size // 2))
