"""Precise per-consumer cross-check of level-JSON keys (scratch, not a pytest)."""
import ast
import json
import pathlib
import sys

sys.path.insert(0, r"E:\nasa")
ROOT = pathlib.Path(r"E:\nasa")

# (file, var) -> scope name
SCOPE_MAP = {
    ("scenes/world_level.py", "self.cfg"): "cfg",
    ("scenes/world_level.py", "self.params"): "params",
    ("scenes/world_level.py", "self.theme"): "theme",
    ("scenes/world_level.py", "self.moment_cfg"): "moment",
    ("core/world_gen.py", "params"): "params",
    ("core/weather.py", "cfg"): "weather",
    ("entities/enemies.py", "cfg"): "cfg",
    ("entities/enemies.py", "params"): "params",
    ("entities/player.py", "cfg"): "params",
    ("entities/player.py", "self.cfg"): "params",
    ("art/world_bg.py", "theme"): "theme",
    ("scenes/tutorial.py", "self.cfg"): "cfg",
    ("scenes/tutorial.py", "self.params"): "params",
    ("scenes/level1.py", "self.cfg"): "cfg",
    ("scenes/level1.py", "self.params"): "params",
    ("scenes/level2.py", "self.cfg"): "cfg",
    ("scenes/level2.py", "self.params"): "params",
    ("scenes/level3.py", "self.cfg"): "cfg",
    ("scenes/level3.py", "self.params"): "params",
    ("scenes/level4.py", "self.cfg"): "cfg",
    ("scenes/level4.py", "self.params"): "params",
    ("scenes/campaign.py", "self.cfg"): "cfg",
    ("scenes/campaign.py", "self.params"): "params",
    ("scenes/campaign.py", "config"): "phase",
    ("scenes/campaign.py", "entry"): "phase",
    ("scenes/briefing.py", "self.cfg"): "cfg",
}


def base_name(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        b = base_name(node.value)
        return b + "." + node.attr if b else node.attr
    return None


def scan(rel):
    p = ROOT / rel
    tree = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Subscript):
            b = base_name(node.value)
            if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
                out.append((node.lineno, b, node.slice.value, "[]"))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "get":
            b = base_name(node.func.value)
            if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                out.append((node.lineno, b, node.args[0].value, ".get"))
    return out


records = []
for rel in sorted(set(k[0] for k in SCOPE_MAP)):
    for lineno, var, key, kind in scan(rel):
        scope = SCOPE_MAP.get((rel, var))
        if scope:
            records.append((rel, lineno, var, scope, key, kind))

LEVELS = {
    "tutorial": ["scenes/tutorial.py"],
    "level1": ["scenes/level1.py", "scenes/campaign.py", "scenes/briefing.py"],
    "level2": ["scenes/level2.py", "scenes/campaign.py", "scenes/briefing.py"],
    "level3": ["scenes/level3.py", "scenes/campaign.py", "scenes/briefing.py"],
    "level4": ["scenes/level4.py", "scenes/campaign.py", "scenes/briefing.py"],
    "mercury": ["scenes/world_level.py", "core/world_gen.py", "core/weather.py",
                "entities/enemies.py", "entities/player.py", "art/world_bg.py"],
    "venus": ["scenes/world_level.py", "core/world_gen.py", "core/weather.py",
              "entities/enemies.py", "entities/player.py", "art/world_bg.py"],
    "mars": ["scenes/world_level.py", "core/world_gen.py", "core/weather.py",
             "entities/enemies.py", "entities/player.py", "art/world_bg.py"],
    "jupiter": ["scenes/world_level.py", "core/world_gen.py", "core/weather.py",
                "entities/enemies.py", "entities/player.py", "art/world_bg.py"],
    "saturn": ["scenes/world_level.py", "core/world_gen.py", "core/weather.py",
               "entities/enemies.py", "entities/player.py", "art/world_bg.py"],
    "uranus": ["scenes/world_level.py", "core/world_gen.py", "core/weather.py",
               "entities/enemies.py", "entities/player.py", "art/world_bg.py"],
    "neptune": ["scenes/world_level.py", "core/world_gen.py", "core/weather.py",
                "entities/enemies.py", "entities/player.py", "art/world_bg.py"],
}


def dig(cfg, scope):
    if scope == "cfg":
        return cfg
    if scope == "params":
        return cfg.get("params") or {}
    if scope == "theme":
        return (cfg.get("params") or {}).get("theme") or {}
    if scope == "moment":
        return (cfg.get("params") or {}).get("moment") or {}
    if scope == "weather":
        return (cfg.get("params") or {}).get("weather") or {}
    if scope == "phase":
        return {}  # handled separately
    return {}


print("=" * 100)
total_missing = 0
for name, files in LEVELS.items():
    cfg = json.loads((ROOT / "data" / "levels" / f"{name}.json").read_text(encoding="utf-8"))
    missing = []
    for rel, lineno, var, scope, key, kind in records:
        if rel not in files:
            continue
        if scope == "phase":
            continue
        target = dig(cfg, scope)
        if key not in target:
            missing.append((rel, lineno, scope, key, kind))
    if missing:
        total_missing += len(missing)
        print(f"\n{name}.json:")
        for rel, lineno, scope, key, kind in sorted(set(missing)):
            print(f"   {rel}:{lineno:<4d} scope={scope:<8s} {kind:<5s} {key!r}")

print("\n--- phase-level keys (per level) ---")
for name in ("level1", "level2", "level3", "level4"):
    cfg = json.loads((ROOT / "data" / "levels" / f"{name}.json").read_text(encoding="utf-8"))
    phases = cfg.get("phases", [])
    print(f"\n{name}.json  phases={[p.get('id') for p in phases]}")
    for rel, lineno, var, scope, key, kind in records:
        if scope != "phase" or rel not in LEVELS[name]:
            continue
        # key must exist on at least one phase (or be phase-specific)
        present = any(key in p for p in phases)
        if not present:
            print(f"   MISSING ON EVERY PHASE  {rel}:{lineno} {key!r}")

print("\nTOTAL missing (non-phase):", total_missing)

print("=" * 100)
print("part sub-keys")
for name in ("mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune"):
    cfg = json.loads((ROOT / "data" / "levels" / f"{name}.json").read_text(encoding="utf-8"))
    part = cfg.get("part")
    ok = isinstance(part, dict) and "name" in part and "color" in part
    print(f"  {name:9s} part={part}  ok={ok}")

print("=" * 100)
print("weather sub-keys read by core/weather.py: type density wind color haze lightning meteors")
for name in ("mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune"):
    cfg = json.loads((ROOT / "data" / "levels" / f"{name}.json").read_text(encoding="utf-8"))
    w = (cfg.get("params") or {}).get("weather")
    print(f"  {name:9s} weather={w}")
