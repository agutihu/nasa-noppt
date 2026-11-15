"""Scratch exploration probe 4 (not a test)."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import sys
sys.path.insert(0, r"E:\nasa")

import json, tempfile, pathlib
import pygame
from core import settings, save, levels, assets, weather
from core.game_state import GameState

TMP = pathlib.Path(tempfile.mkdtemp())
print("=== weather hash across processes (PYTHONHASHSEED) ===")
import subprocess
for seed in ("0", "1", "2"):
    env = dict(os.environ, PYTHONHASHSEED=seed)
    out = subprocess.run(
        [sys.executable, "-c",
         "import os;os.environ.setdefault('SDL_VIDEODRIVER','dummy');"
         "import sys;sys.path.insert(0, r'E:\\nasa');"
         "from core import weather;"
         "w=weather.Weather({'type':'dust','density':3});"
         "print([round(p['x'],4) for p in w.particles])"],
        capture_output=True, text=True, env=env)
    print("  seed", seed, out.stdout.strip(), out.stderr.strip()[:200])

print("=== assets.image with display mode ===")
imgs = TMP / "images"
imgs.mkdir(parents=True, exist_ok=True)
surf = pygame.Surface((16, 16))
pygame.image.save(surf, str(imgs / "test.png"))
old = settings.ASSETS
settings.ASSETS = TMP
try:
    pygame.display.set_mode((320, 240))
except Exception as e:
    print("set_mode failed", e)
print("image with display:", assets.image("test.png"))
print("image scaled:", assets.image("test.png", 2))
print("image with bad scale 0:", assets.image("test.png", 0))
settings.ASSETS = old

print("=== raw convert_alpha error ===")
try:
    s = pygame.image.load(str(imgs / "test.png"))
    s.convert_alpha()
except Exception as e:
    print("  ->", type(e).__name__, e)

print("=== levels malformed data ===")
bad = TMP / "baddata"
(bad / "levels").mkdir(parents=True, exist_ok=True)
(bad / "dialogue").mkdir(parents=True, exist_ok=True)
olddata = settings.DATA
settings.DATA = bad
for name, content in [
    ("mission.json", "{ not json"),
    ("mission.json", "[1,2]"),
    ("mission.json", '{"levels": []}'),
    ("mission.json", '{"levels": [{"id":"x"}]}'),
    ("planets.json", '{"planets": []}'),
    ("planets.json", '{"planets": [{"id":"x"}]}'),
]:
    (bad / name).write_text(content, encoding="utf-8")
    try:
        levels.load_mission()
    except Exception as e:
        print(" ", name, content[:28], "->", type(e).__name__, e)
    try:
        levels.load_planets()
    except Exception as e:
        print(" ", name, content[:28], "planets ->", type(e).__name__, e)
# missing dir entirely
settings.DATA = TMP / "does_not_exist"
try:
    levels.load_mission()
except Exception as e:
    print("  missing dir ->", type(e).__name__, e)
try:
    levels.load_planets()
except Exception as e:
    print("  missing dir planets ->", type(e).__name__, e)
settings.DATA = olddata

print("=== from_dict edge ===")
for payload in [
    {"best_times": [1, 2]},
    {"best_times": {"a": "zz"}},
    {"facts": "abc"},
    {"inventory": 5},
    {"difficulty": 123},
    {"player_name": None},
    {"current_level": 5},
    {"outcome": 7},
    {"mission_started": "no"},
]:
    try:
        g = GameState.from_dict(payload)
        print("  ", payload, "->", g.difficulty, g.player_name, g.outcome, g.current_level)
    except Exception as e:
        print("  ", payload, "-> RAISES", type(e).__name__, e)

print("=== save edge: path is a directory ===")
settings.SAVE_FILE = TMP / "adir"
(TMP / "adir").mkdir(exist_ok=True)
print("write to dir:", save.write({"a": 1}))
print("read from dir:", save.read())
print("exists:", save.exists())
settings.SAVE_FILE = TMP / "x.savegame"
print("write odd suffix:", save.write({"a": 1}), list(TMP.glob("x*")))

print("=== weather odd configs ===")
w = weather.Weather({"type": "dust", "density": 5, "wind": [1, 2, 3]})
print("3-tuple wind ok?")
try:
    w.update(0.016)
except Exception as e:
    print("  ->", type(e).__name__, e)
w2 = weather.Weather({"type": "acid_rain", "density": 3, "color": [255, 0, 0]})
scr = pygame.Surface((settings.WIDTH, settings.HEIGHT))
w2.draw(scr)
print("3-color rain draw ok")
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
w5.draw(scr)
print("draw with no particles returns early (flash not drawn)")
