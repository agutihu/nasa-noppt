"""Scratch exploration probe 5 (not a test)."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import sys
sys.path.insert(0, r"E:\nasa")

import json, tempfile, pathlib
import pygame
from core import settings, levels, weather, assets

TMP = pathlib.Path(tempfile.mkdtemp())

print("=== weather rest ===")
scr = pygame.Surface((settings.WIDTH, settings.HEIGHT))
w3 = weather.Weather({"type": "heat", "density": 3, "color": [255, 140, 60], "meteors": True})
for _ in range(30):
    w3.update(0.1)
w3.draw(scr)
print("heat+meteors ok, streaks:", len(w3.meteor_streaks))
w4 = weather.Weather({"type": "snow", "density": 3, "haze": [1, 2, 3, 10]})
w4.update(0.016)
w4.draw(scr)
w4.draw_haze(scr)
print("snow+haze ok")
w5 = weather.Weather({"type": "none", "density": 0, "lightning": True})
for _ in range(200):
    w5.update(0.05)
print("lightning flash:", w5.flash, "particles:", len(w5.particles))
before = scr.get_at((10, 10))
w5.draw(scr)
after = scr.get_at((10, 10))
print("flash overlay drawn?", before != after)

w6 = weather.Weather({"type": "dust", "density": -5})
print("negative density particles:", len(w6.particles))
w7 = weather.Weather({"type": "unknown_kind", "density": 5})
w7.update(0.016)
w7.draw(scr)
print("unknown kind ok (falls to dust branch)")
w8 = weather.Weather({"type": "dust", "density": 5, "wind": {"a": 1, "b": 2}})
try:
    w8.update(0.016)
    print("dict wind ok")
except Exception as e:
    print("dict wind ->", type(e).__name__, e)
w9 = weather.Weather({"type": "acid_rain", "density": 3, "color": [255, 0, 0], "lightning": True})
w9.update(0.016)
w9.draw(scr)
print("rain+lightning ok")
w10 = weather.Weather({"type": "ice_glitter", "density": 3})
w10.update(0.016)
w10.draw(scr)
print("ice_glitter ok")

print("=== levels params_for AttributeError ===")
try:
    levels.params_for({"params": {"difficulty": 5}}, "easy")
except Exception as e:
    print(" ->", type(e).__name__, e)
try:
    levels.params_for({"params": {"difficulty": ["a"]}}, "easy")
except Exception as e:
    print(" ->", type(e).__name__, e)
try:
    levels.params_for({"params": {"difficulty": {"easy": 5}}}, "easy")
except Exception as e:
    print(" ->", type(e).__name__, e)
print("params_for nested difficulty values:", levels.params_for({"params": {"difficulty": {"easy": {"x": 1}}}}, "easy"))

print("=== settings duplicate definitions ===")
import inspect, core.settings as st
src = inspect.getsource(st)
for name in ("PLAYABLE_SCENES",):
    print(name, "count:", src.count(name + " ="))
print("PLAYABLE_SCENES value:", st.PLAYABLE_SCENES)
print("LEVEL_IDS value:", st.LEVEL_IDS)

print("=== required_parts cache ===")
print("cache info:", levels._required_parts_cached.cache_info())
