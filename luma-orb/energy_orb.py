# energy_orb.py - V2 Visual Cortex
import pygame
import math

class EnergyOrb:
    def __init__(self):
        pass

    def draw(self, screen, center, radius, t, base_color, is_thinking, mode, cfg, ops, chat_active, resp, voice):
        color = cfg.mode_palette.get(mode, base_color)
        
        # --- TOP-RIGHT METADATA ---
        font = pygame.font.SysFont("Consolas", 14)
        metadata = [
            f"AGNT: L.U.M.A. V2", # Lau’s Universal Management Agent [cite: 2026-02-11]
            f"MODE: {mode}",
            f"STAT: { 'THINKING' if is_thinking else 'LISTENING' if not voice.is_speaking else 'SPEAKING' }",
            f"HUB: HERNING_STATION"
        ]
        for i, text in enumerate(metadata):
            txt_surf = font.render(text, True, color)
            screen.blit(txt_surf, (cfg.width - 180, 20 + (i * 18)))

        # --- CENTRAL ENERGY ORB ---
        # Main Outer Ring
        pygame.draw.circle(screen, color, center, radius, 2)
        
        # Rotating Technical Arcs (The "Luma" Ring)
        rect = pygame.Rect(center[0]-radius-10, center[1]-radius-10, (radius+10)*2, (radius+10)*2)
        pygame.draw.arc(screen, color, rect, t, t + 1.5, 3) # Bottom Arc
        pygame.draw.arc(screen, color, rect, t + 3.14, t + 4.64, 3) # Top Arc

        # Inner Reasoning Pulse
        pulse_val = radius - 15 + (math.sin(t * 5) * 5)
        if is_thinking:
            # Shift to Magenta/Cobalt when reasoning
            pygame.draw.circle(screen, (180, 0, 255), center, int(pulse_val), 0)
        else:
            pygame.draw.circle(screen, color, center, int(pulse_val), 1)