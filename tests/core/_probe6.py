"""Scratch exploration probe 6 (not a test)."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import sys
sys.path.insert(0, r"E:\nasa")

import pygame
from core import settings, weather

scr = pygame.Surface((settings.WIDTH, settings.HEIGHT))
scr.fill((0, 0, 0))
w = weather.Weather({"type": "none", "density": 0, "lightning": True})
w.flash = 1.0
before = scr.get_at((10, 10))
w.draw(scr)
after = scr.get_at((10, 10))
print("no-particle flash drawn?", before != after, before, after)

scr2 = pygame.Surface((settings.WIDTH, settings.HEIGHT))
scr2.fill((0, 0, 0))
w2 = weather.Weather({"type": "dust", "density": 5, "lightning": True})
w2.flash = 1.0
before2 = scr2.get_at((10, 10))
w2.draw(scr2)
after2 = scr2.get_at((10, 10))
print("with-particle flash drawn?", before2 != after2, before2, after2)

print("=== weather update: particle wrap ===")
w3 = weather.Weather({"type": "dust", "density": 1})
p = w3.particles[0]
p["x"] = -1000.0
w3.update(0.016)
print("x wrapped to", p["x"], "(expect in [-60, WIDTH+60])")

print("=== weather update: big dt ===")
w4 = weather.Weather({"type": "acid_rain", "density": 3})
w4.update(5.0)
print("ok, t =", w4.t)

print("=== weather: y reset for non-heat kinds ===")
w5 = weather.Weather({"type": "snow", "density": 1})
p5 = w5.particles[0]
p5["y"] = -1000.0
w5.update(0.016)
print("snow y after going above top:", p5["y"], "(no reset for snow -> drifts off screen)")
