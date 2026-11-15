import os, sys, math
os.environ.setdefault("SDL_VIDEODRIVER","dummy"); os.environ.setdefault("SDL_AUDIODRIVER","dummy")
sys.path.insert(0, r"E:\nasa")
import pygame
from core import settings, levels, text
from core.game_state import GameState
pygame.init(); pygame.display.set_mode((settings.WIDTH, settings.HEIGHT))

print("== F: _draw_part double camera subtraction ==")
import inspect, re
src = inspect.getsource(__import__("scenes.world_level", fromlist=["x"]).WorldLevelBase._draw_part)
for i, line in enumerate(src.splitlines()):
    if "camera[0]" in line or "camera[1]" in line:
        print("   ", line.strip())

print("== G: part_count polluted by non-part inventory ==")
s = GameState()
for junk in ["ration","medkit","tool"]:
    s.add_item(junk)
print("   inventory:", s.inventory)
print("   part_count:", s.part_count, "(real parts: 0)")
print("   required:", len(s.required_parts()))
# simulate a player who picked 3 vending items + 4 real parts
s2 = GameState()
for junk in ["ration","medkit","tool"]: s2.add_item(junk)
for p in levels.required_parts()[:4]: s2.add_part(p)
print("   with 3 junk + 4 parts -> part_count:", s2.part_count, "all_parts:", s2.all_parts(), "(should be False)")

print("== H: status_line ==")
print("  ", s2.status_line())

print("== I: settings.PLAYABLE_SCENES shadowing ==")
import core.settings as st
print("   PLAYABLE_SCENES =", st.PLAYABLE_SCENES)

print("== J: required_parts fallback when planets.json unreadable ==")
import core.levels as L
L._required_parts_cached.cache_clear()
orig = L.load_planets
L.load_planets = lambda: (_ for _ in ()).throw(L.DataError("boom"))
g = GameState(); g.inventory = ["x","y"]
print("   required_parts() fallback ->", g.required_parts(), "(BUG: returns collected parts)")
L.load_planets = orig
L._required_parts_cached.cache_clear()
