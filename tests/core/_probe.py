"""Scratch exploration probe (not a test). Run: python E:\nasa\tests\core\_probe.py"""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import sys
sys.path.insert(0, r"E:\nasa")

import json
from core import levels, settings, save
from core.game_state import GameState

print("LEVEL_IDS:", settings.LEVEL_IDS)
print("mission level ids:", levels.level_ids())
print("PLANET_ORDER:", levels.PLANET_ORDER)
print("required_parts:", levels.required_parts())
print("next_level('mercury'):", levels.next_level("mercury"))
print("next_level('outpost'):", levels.next_level("outpost"))
print("level_number('mars'):", levels.level_number("mars"))
print("previous_mission('venus'):", levels.previous_mission("venus"))
print("previous_mission('mercury'):", levels.previous_mission("mercury"))
print("previous_mission('earth'):", levels.previous_mission("earth"))

st = GameState()
print("hearts easy/normal/hard:")
for d in ("easy", "normal", "hard"):
    st.difficulty = d
    print("  ", d, st.hearts(), st.scale_speed(100))
print("part_count", st.part_count, "required_parts", st.required_parts())
print("all_parts (empty inv):", st.all_parts())
print("status_line:", st.status_line())
print("progress_line:", st.progress_line())
print("next_level_id:", st.next_level_id())

st2 = GameState()
st2.tutorial_done = True
print("is_unlocked('mercury') with tutorial:", st2.is_unlocked("mercury"))
print("is_unlocked('venus') with tutorial only:", st2.is_unlocked("venus"))
st2.levels_done.append("mercury")
print("is_unlocked('venus') after mercury:", st2.is_unlocked("venus"))
print("is_unlocked('outpost') tutorial done:", st2.is_unlocked("outpost"))
print("is_unlocked('bogus'):", st2.is_unlocked("bogus"))

planets = levels.planet_index()
print("planet keys:", list(planets))
print("is_unlocked(venus dict):", st2.is_unlocked(planets["venus"]))
print("is_unlocked(earth dict):", st2.is_unlocked(planets["earth"]))

# to_dict / from_dict round trip
d = st2.to_dict()
print("to_dict keys:", sorted(d.keys()))
st3 = GameState.from_dict(d)
print("roundtrip equal-ish:", st3.difficulty, st3.text_scale, st3.levels_done)

# complete_level
print("complete_level('outpost'):", st2.complete_level("outpost", 12.5))
print("levels_done:", st2.levels_done, "best_times:", st2.best_times)

# corrupt from_dict
print("from_dict junk:", GameState.from_dict({"photos": "abc"}).photos)
try:
    print("from_dict photos=abc ->", GameState.from_dict({"photos": "abc"}))
except Exception as e:
    print("from_dict photos=abc raises", type(e).__name__, e)

print("from_dict best_times junk:")
try:
    print(GameState.from_dict({"best_times": {"a": "zz"}}))
except Exception as e:
    print("  raises", type(e).__name__, e)

print("from_dict best_times not dict:")
try:
    print(GameState.from_dict({"best_times": [1, 2]}))
except Exception as e:
    print("  raises", type(e).__name__, e)

print("from_dict player_name long:", GameState.from_dict({"player_name": "x" * 100}).player_name)
print("from_dict elapsed junk:")
try:
    print(GameState.from_dict({"elapsed": "abc"}))
except Exception as e:
    print("  raises", type(e).__name__, e)

print("from_dict version diff -> load() returns False")
