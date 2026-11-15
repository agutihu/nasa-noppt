import os, sys, json, shutil, tempfile
os.environ.setdefault("SDL_VIDEODRIVER","dummy"); os.environ.setdefault("SDL_AUDIODRIVER","dummy")
sys.path.insert(0, r"E:\nasa")
from core import settings, save
from core.game_state import GameState

print("== A: tutorial_done persistence ==")
s = GameState(); s.tutorial_done = True; s.mark_level_done("mercury")
d = s.to_dict()
print("  to_dict has tutorial_done:", "tutorial_done" in d)
s2 = GameState.from_dict(d)
print("  after from_dict tutorial_done:", s2.tutorial_done, "(expected True)")

print("== B: status_line denominator ==")
s3 = GameState(); s3.inventory = ["a","b","c"]
print("  status_line:", s3.status_line(), "(expected 0/7 style)")

print("== C: all_parts with junk inventory ==")
s4 = GameState(); s4.inventory = ["junk1","junk2","junk3"]
print("  required:", len(s4.required_parts()))
print("  all_parts with 3 junk items:", s4.all_parts(), "(expected False)")

print("== D: hearts per difficulty ==")
for d_ in ("easy","normal","hard"):
    g = GameState(difficulty=d_); print("  ", d_, "->", g.hearts())

print("== E: malformed save crash ==")
backup = settings.SAVE_FILE.read_bytes() if settings.SAVE_FILE.is_file() else None
for bad in [ {"version":2,"volume":"abc"}, {"version":2,"best_times":[1,2]}, {"version":2,"photos":"x"} ]:
    settings.SAVE_FILE.write_text(json.dumps(bad))
    try:
        g = GameState(); ok = g.load(); print("  ", bad, "-> load ok, returned", ok)
    except Exception as e:
        print("  ", bad, "-> CRASH", type(e).__name__, e)
if backup is not None:
    settings.SAVE_FILE.write_bytes(backup)
else:
    settings.SAVE_FILE.unlink(missing_ok=True)
