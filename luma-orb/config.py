import pygame

class Config:
    def __init__(self):
        # UI Settings
        self.width, self.height = 1000, 700
        self.radius = 120
        
        # Colors (Nordic Tech Palette)
        self.bg_color = (10, 10, 15)      # Midnight
        self.grid_color = (30, 30, 45)    # Low-alpha grid
        self.orb_idle = (0, 210, 255)     # Electric Cyan
        self.orb_thinking = (0, 255, 180) # Aurora Green (Deep Logic)
        self.orb_speaking = (255, 0, 150) # Magenta/Pulse
        
        self.mode_palette = {
            "deepwork": (0, 100, 255),     # Focused Cobalt
            "work": (0, 255, 180),         # Aurora Green
            "casual": (255, 165, 0),       # Amber
            "home project": (200, 0, 255), # Purple Spark
            "away": (150, 150, 150)        # Ghost Grey
        }
        
        # Paths & AI
        self.local_model = "phi3"
        self.ollama_url = "http://localhost:11434/api/generate"
        self.wake_word = "luma"
        
        # Engineering Constraints
        self.max_history = 6