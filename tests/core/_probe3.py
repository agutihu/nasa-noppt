"""Scratch exploration probe 3 (not a test)."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import sys
sys.path.insert(0, r"E:\nasa")

import json, tempfile, pathlib
import pygame
from core import settings, save, world_gen, weather, assets
from core.game_state import GameState

TMP = pathlib.Path(tempfile.mkdtemp())
settings.SAVE_FILE = TMP / "savegame.json"

print("=== tutorial_done round trip ===")
st = GameState()
st.tutorial_done = True
st.levels_done.append("mercury")
st.save()
print("saved json keys:", sorted(json.loads(settings.SAVE_FILE.read_text()).keys()))
print("tutorial_done in saved json:", "tutorial_done" in json.loads(settings.SAVE_FILE.read_text()))
st2 = GameState()
print("load() ->", st2.load())
print("after load tutorial_done:", st2.tutorial_done, "levels_done:", st2.levels_done)

print("=== volume 0 ===")
st3 = GameState()
st3.volume = 0.0
st3.save()
print("saved volume:", json.loads(settings.SAVE_FILE.read_text())["volume"])
st4 = GameState()
st4.load()
print("restored volume:", st4.volume, "(expected 0.0)")

print("=== text_scale 0.8 ===")
st5 = GameState(text_scale=0.8)
st5.save()
st6 = GameState()
st6.load()
print("restored text_scale:", st6.text_scale)

print("=== save.write non-serializable ===")
try:
    print(save.write({"a": object()}))
except Exception as e:
    print("save.write ->", type(e).__name__, e)

print("=== load() corrupt but version ok ===")
settings.SAVE_FILE.write_text(json.dumps({"version": 2, "photos": "abc"}), encoding="utf-8")
try:
    print(GameState().load())
except Exception as e:
    print("load ->", type(e).__name__, e)

print("=== load() version as junk ===")
settings.SAVE_FILE.write_text(json.dumps({"version": "abc"}), encoding="utf-8")
try:
    print(GameState().load())
except Exception as e:
    print("load ->", type(e).__name__, e)

print("=== all_parts with junk items ===")
st7 = GameState()
for i in range(7):
    st7.add_item(f"junk{i}")
print("part_count", st7.part_count, "all_parts", st7.all_parts())
print("status_line:", st7.status_line())

print("=== reset_mission keeps tutorial_done? ===")
st8 = GameState()
st8.tutorial_done = True
st8.reset_mission()
print("tutorial_done after reset:", st8.tutorial_done)
print("save file exists after reset:", settings.SAVE_FILE.exists())

print("=== world_gen tiny ===")
w = world_gen.generate("t", {"seed": 1, "world_length": 100})
print("platforms:", [(p.x, p.y, p.width, p.height) for p in w["platforms"]])
print("part_pos", w["part_pos"], "exit_pos", w["exit_pos"], "checkpoints", w["checkpoints"])
w0 = world_gen.generate("t", {"seed": 1, "world_length": 0})
print("wl=0 platforms:", [(p.x, p.y, p.width, p.height) for p in w0["platforms"]])
print("wl=0 part_pos", w0["part_pos"], "exit", w0["exit_pos"])
wsmall = world_gen.generate("t", {"seed": 1, "world_length": 1500})
print("wl=1500 pickups:", len(wsmall["pickups"]), "props:", len(wsmall["props"]))
print("wl=1500 part_pos", wsmall["part_pos"], "exit", wsmall["exit_pos"])

print("=== weather determinism ===")
a = weather.Weather({"type": "dust", "density": 5})
b = weather.Weather({"type": "dust", "density": 5})
print("same seed positions:", [p["x"] for p in a.particles] == [p["x"] for p in b.particles])

print("=== assets.image without display mode ===")
imgs = TMP / "images"
imgs.mkdir(parents=True, exist_ok=True)
surf = pygame.Surface((16, 16))
pygame.image.save(surf, str(imgs / "test.png"))
old = settings.ASSETS
settings.ASSETS = TMP
print("path:", assets.path("images", "test.png"))
try:
    print("image:", assets.image("test.png"))
except Exception as e:
    print("image ->", type(e).__name__, e)
print("has display mode:", pygame.display.get_init(), pygame.display.get_surface())
settings.ASSETS = old

print("=== assets.path traversal ===")
print("path('..','core','game_state.py'):", assets.path("..", "core", "game_state.py"))
print("path():", assets.path())

print("=== scene manager ===")
from core.scene import Game, Scene, SceneManager
state = GameState()
game = Game(pygame.Surface((1280, 720)), pygame.Surface((1280, 720)), state)
mgr = game.manager
class S(Scene):
    name = "s"
mgr.register("s", S)
sc = mgr.switch("s")
print("current:", mgr.current_name, "stack len", len(mgr.stack))
mgr.push("s")
print("stack len", len(mgr.stack), "current", mgr.current_name)
mgr.pop()
print("after pop stack", len(mgr.stack))
try:
    mgr.switch("nope")
except Exception as e:
    print("switch unknown ->", type(e).__name__, e)
try:
    mgr.pop()
    mgr.pop()
except Exception as e:
    print("pop empty ->", type(e).__name__, e)
print("scale_mouse:", game.scale_mouse((640, 360)))
print("elapsed after update:", state.elapsed)
