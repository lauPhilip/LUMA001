import pygame
import time
import winsound
from config import Config
from luma import Luma
from energy_orb import EnergyOrb
from luma_ops import LumaOps
import os
from voice_engine import VoiceEngine
import sys
import pathlib

# 1. ANCHOR TO THE PARENT VENV
# We go up one level from 'luma-orb' to 'LUMA001' to find the .venv
base_path = pathlib.Path(__file__).parent.parent.absolute()
venv_scripts = base_path / ".venv" / "Scripts"

if venv_scripts.exists():
    # Force the local environment to recognize the shared DLLs in the parent folder
    os.add_dll_directory(str(venv_scripts.resolve()))
    os.environ["PATH"] = str(venv_scripts.resolve()) + os.pathsep + os.environ["PATH"]
    print(f"LUMA_LOG: Nerve-link established with parent .venv at {venv_scripts}")
else:
    print("LUMA_LOG: WARNING - Could not find the .venv in the parent directory.")
    
# Silence Hugging Face symlink warnings and auth warnings
os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'

class ChatInterface:
    def __init__(self, cfg):
        self.active = False
        self.text = ""
        self.font = pygame.font.SysFont("Consolas", 20)
        self.cfg = cfg

    def handle_event(self, event, luma):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB: # Toggle Protocol
                self.active = not self.active
                self.text = ""
                
                # --- VOICE KILL-SWITCH ---
                # If you hit TAB while I'm talking, I'll stop immediately.
                if self.active and luma.voice_engine:
                    luma.voice_engine.stop() 
            
            elif self.active:
                if event.key == pygame.K_RETURN:
                    # Explicitly tell me this is a 'chat' command
                    luma.receive_input(self.text, method="chat")
                    self.text = ""
                    self.active = False
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    self.text += event.unicode
    def draw(self, screen):
        """The missing draw method."""
        if self.active:
            # Discreet translucent input bar
            overlay = pygame.Surface((self.cfg.width - 100, 40), pygame.SRCALPHA)
            overlay.fill((20, 20, 30, 200)) 
            screen.blit(overlay, (50, self.cfg.height - 100))
            
            # Render the current buffer
            input_surf = self.font.render(f"> {self.text}_", True, (0, 210, 255))
            screen.blit(input_surf, (70, self.cfg.height - 90))

def cleanup(luma_instance):
    """The shutdown protocol for L.U.M.A."""
    # Trigger the session summary before closing
    # We pass her the last response text as a highlight
    summary_msg = luma_instance.skills.save_session_summary([luma_instance.response_text])
    print(f"LUMA_LOG: {summary_msg}") #
    
    # Optional: A quick parting chime
    import winsound
    winsound.Beep(1000, 100)
    winsound.Beep(800, 150)

def show_splash_screen(cfg):
    splash_screen = pygame.display.set_mode((cfg.width, cfg.height), pygame.NOFRAME)
    
    # --- HARDWARE START SOUND ---
    boot_notes = [800, 1200, 1600] 
    for note in boot_notes:
        winsound.Beep(note, 60)
        time.sleep(0.02)

    font_large = pygame.font.SysFont("Consolas", 40, bold=True)
    font_small = pygame.font.SysFont("Consolas", 18)
    
    # 1. LOAD ASSETS ONCE (Optimization)
    icon_path = 'luma-orb/assets/LUMA.png'
    try:
        icon_surf = pygame.image.load(icon_path).convert_alpha()
        icon_surf = pygame.transform.smoothscale(icon_surf, (150, 150))
        # icon_surf.set_alpha(200) # Optional: slightly transparent for tech vibe
    except Exception as e:
        print(f"LUMA_LOG: Icon load failed: {e}")
        icon_surf = None

    start_time = time.time()
    
    while time.time() - start_time < 4:
        splash_screen.fill((10, 10, 15)) 
        
        center_x = cfg.width // 2
        center_y = cfg.height // 2
        
        # 2. RENDER ICON (100px above text center)
        if icon_surf:
            icon_rect = icon_surf.get_rect(center=(center_x, center_y - 120))
            splash_screen.blit(icon_surf, icon_rect)
        
        # 3. RENDER TEXT
        title = font_large.render("LUMA", True, (0, 210, 255))
        protocol = font_small.render("F.R.I.D.A.Y. PROTOCOL // VERSION 1.0", True, (0, 255, 180))
        
        # Centering the text surfaces
        title_rect = title.get_rect(center=(center_x, center_y))
        protocol_rect = protocol.get_rect(center=(center_x, center_y + 40))
        
        splash_screen.blit(title, title_rect)
        splash_screen.blit(protocol, protocol_rect)
        
        # 4. SIMULATED BOOT LOG
        boot_steps = [
            "> Initializing neural links...",
            "> Calibrating sensory array...",
            "> Establishing Herning local uplink...",
            "> Initializing skill assets...",
            "> Systems green."
        ]
        
        elapsed = time.time() - start_time
        for i, step in enumerate(boot_steps):
            if elapsed > (i * 1): # Sped up slightly for a snappier feel
                step_text = font_small.render(step, True, (80, 80, 120))
                splash_screen.blit(step_text, (50, cfg.height - 150 + (i * 20)))
        
        pygame.display.flip()
        
    pygame.display.quit()

def main():
    pygame.init()
    cfg = Config()
    
    show_splash_screen(cfg)
    
    pygame.init()
    pygame.display.set_caption("L.U.M.A. V001")
    
    # 1. Set the OS-Level Icon
    icon_path = 'luma-orb/assets/LUMA.png'
    try:
        app_icon = pygame.image.load(icon_path)
        pygame.display.set_icon(app_icon)
    except Exception as e:
        print(f"LUMA_LOG: Could not load taskbar icon: {e}")
    screen = pygame.display.set_mode((cfg.width, cfg.height))
    luma = Luma(cfg)
    voice = VoiceEngine(luma.receive_input)
    luma.voice_engine = voice
    
    # STARTUP BRIEFING: Trigger as the system goes live
    luma.startup_briefing()
    
    voice.start_listening(luma)
    orb = EnergyOrb()
    chat = ChatInterface(cfg)
    
    clock = pygame.time.Clock()
    running = True

    while running:
        t = time.time()
        screen.fill((5, 5, 10)) # Deep space background
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                luma.refresh_knowledge()
                luma.skills.save_session_summary([luma.response_text]) #
                running = False
            chat.handle_event(event, luma)

        # Draw HUD with Ops Progress
        orb.draw(screen, (cfg.width//2, cfg.height//2), cfg.radius, t, 
                 cfg.orb_idle, luma.is_thinking, luma.current_mode, cfg, 
                 luma.ops, chat.active, luma.response_text, voice)
        
        chat.draw(screen) # Layer the chat interface
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()