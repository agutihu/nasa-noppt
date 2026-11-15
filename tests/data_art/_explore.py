"""Scratch exploration script (not part of the pytest suite)."""
import json
import os
import pathlib
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, r"E:\nasa")

ROOT = pathlib.Path(r"E:\nasa")
DATA = ROOT / "data"

print("=" * 70)
print("1. JSON parse check")
for p in sorted(DATA.rglob("*.json")):
    try:
        json.loads(p.read_text(encoding="utf-8"))
        print(f"  OK   {p.relative_to(ROOT)}")
    except Exception as exc:
        print(f"  FAIL {p.relative_to(ROOT)}: {type(exc).__name__}: {exc}")

print("=" * 70)
print("2. planets.json")
planets_cfg = json.loads((DATA / "planets.json").read_text(encoding="utf-8"))
ids = [p["id"] for p in planets_cfg["planets"]]
print("  ids:", ids)
print("  dup ids:", [i for i in set(ids) if ids.count(i) > 1])
parts = [p.get("part") for p in planets_cfg["planets"] if p.get("part")]
print("  parts:", parts)
print("  order:", planets_cfg.get("order"))

print("=" * 70)
print("3. level files vs planet ids")
for p in sorted((DATA / "levels").glob("*.json")):
    cfg = json.loads(p.read_text(encoding="utf-8"))
    print(f"  {p.stem:10s} id={cfg.get('id')!r:14s} dialogue={cfg.get('dialogue')!r}")

print("=" * 70)
print("4. dialogue triggers per file")
for p in sorted((DATA / "dialogue").glob("*.json")):
    cfg = json.loads(p.read_text(encoding="utf-8"))
    trigs = []
    for entry in cfg.get("lines", []):
        t = entry.get("trigger", "start")
        if t not in trigs:
            trigs.append(t)
    print(f"  {p.stem:10s} topkeys={sorted(cfg.keys())} triggers={trigs}")

print("=" * 70)
print("5. level phase dialogue triggers vs dialogue files")
for name in ("level1", "level2", "level3", "level4"):
    cfg = json.loads((DATA / "levels" / f"{name}.json").read_text(encoding="utf-8"))
    dlg_path = DATA / "dialogue" / cfg["dialogue"].replace("dialogue/", "")
    dcfg = json.loads(dlg_path.read_text(encoding="utf-8"))
    have = {e.get("trigger", "start") for e in dcfg.get("lines", [])}
    used = []
    for ph in cfg.get("phases", []):
        if ph.get("dialogue_trigger"):
            used.append(("phase:" + ph["id"], ph["dialogue_trigger"]))
        if ph.get("on_correct"):
            used.append((ph["id"] + ":on_correct", ph["on_correct"]))
        if ph.get("on_wrong"):
            used.append((ph["id"] + ":on_wrong", ph["on_wrong"]))
    for label, t in used:
        flag = "OK " if t in have else "MISS"
        print(f"  {flag} {name} {label:34s} -> {t!r}")

print("=" * 70)
print("6. tutorial triggers")
tut = json.loads((DATA / "dialogue" / "tutorial.json").read_text(encoding="utf-8"))
have = {e.get("trigger", "start") for e in tut.get("lines", [])}
for t in ("start", "marker", "crate", "win", "hint", "hint_prompt", "idle"):
    print(f"  {'OK ' if t in have else 'MISS'} tutorial trigger {t!r}")

print("=" * 70)
print("7. world-level dialogue triggers required by world_level.py")
need = ("start", "hint", "death_3", "moment", "part", "win")
for pid in ("mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune"):
    cfg = json.loads((DATA / "dialogue" / f"{pid}.json").read_text(encoding="utf-8"))
    have = {e.get("trigger", "start") for e in cfg.get("lines", [])}
    missing = [t for t in need if t not in have]
    print(f"  {pid:9s} missing={missing}")

print("=" * 70)
print("8. LEVEL_KEYS presence (core/levels.py)")
need_keys = ("id", "name", "dialogue", "params", "objective")
for p in sorted((DATA / "levels").glob("*.json")):
    cfg = json.loads(p.read_text(encoding="utf-8"))
    missing = [k for k in need_keys if k not in cfg]
    print(f"  {p.stem:10s} missing={missing}")

print("=" * 70)
print("9. params.moment")
for p in sorted((DATA / "levels").glob("*.json")):
    cfg = json.loads(p.read_text(encoding="utf-8"))
    if cfg.get("style") == "world":
        m = (cfg.get("params") or {}).get("moment")
        print(f"  {p.stem:10s} moment={m}")
