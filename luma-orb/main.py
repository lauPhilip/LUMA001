# main.py
import queue
import socket
import threading
import time

import pygame

from luma import Luma, LumaConfig
from energy_orb import EnergyOrb, EnergyOrbStyle

icon = pygame.image.load("luma.jpg")
pygame.display.set_icon(icon)

ENABLE_TCP_INPUT = True
TCP_HOST = "0.0.0.0"
TCP_PORT = 5050

event_q: "queue.Queue[tuple[str, float, str]]" = queue.Queue()


def tcp_listener(host: str, port: int) -> None:
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((host, port))
    srv.listen(5)

    while True:
        conn, addr = srv.accept()
        with conn:
            try:
                data = conn.recv(4096)
                if not data:
                    continue
                msg = data.decode("utf-8", errors="replace").strip()
                if msg:
                    event_q.put(("BOT_INPUT", time.time(), f"{addr[0]}: {msg}"))
            except Exception:
                continue


def main() -> None:
    cfg = LumaConfig(
        width=800,
        height=480,
        radius=110,   # fixed orb size
    )

    luma = Luma(cfg)

    orb = EnergyOrb(EnergyOrbStyle())

    start_time = time.time()

    pygame.init()
    pygame.display.set_caption("Luma")
    screen = pygame.display.set_mode((cfg.width, cfg.height))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 24)

    if ENABLE_TCP_INPUT:
        threading.Thread(target=tcp_listener, args=(TCP_HOST, TCP_PORT), daemon=True).start()

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        now = time.time()
        t = now - start_time

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    running = False
                elif ev.key == pygame.K_SPACE:
                    luma.receive_input("SPACE (simulated input)")

        while True:
            try:
                ev_type, ev_time, ev_text = event_q.get_nowait()
            except queue.Empty:
                break
            if ev_type == "BOT_INPUT":
                luma.receive_input(ev_text)

        #luma.update(dt)

        # Background (slightly lifted helps the glass effect)
        screen.fill((12, 12, 16))

        attentive = luma.is_attentive(now)
        if attentive:
            #base_rgb = (40, 220, 120)   # green state
            state = "GREEN (attentive)"
        else:
            #base_rgb = (60, 140, 255)   # blue state
            state = "BLUE (idle)"
            
        fixed_radius = cfg.radius
        center = (cfg.width // 2, cfg.height // 2)

        orb.draw(
            screen,
            center=center,
            radius=fixed_radius,
            t=t,
        )



        # Minimal HUD
        screen.blit(font.render(f"Luma: {state}", True, (235, 235, 235)), (12, 12))
        screen.blit(font.render("SPACE = simulate input | ESC = quit", True, (165, 165, 165)), (12, 40))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
