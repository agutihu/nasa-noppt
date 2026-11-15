"""Scratch AST scan for level-data key reads (not part of the pytest suite)."""
import ast
import json
import os
import pathlib
import sys

sys.path.insert(0, r"E:\nasa")
ROOT = pathlib.Path(r"E:\nasa")

# variable names that hold level-data dicts
LEVEL_VARS = {"params", "cfg", "config", "theme", "moment_cfg", "phase_cfg",
              "entry", "self.params", "self.cfg", "self.theme", "self.moment_cfg"}

SRC_DIRS = ["scenes", "core", "entities", "ui", "art"]


def base_name(node):
    """Return the dotted-ish base name of an expression, or None."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return base_name(node.value) + "." + node.attr
    return None


def scan(path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    out = []
    for node in ast.walk(tree):
        # X["key"]
        if isinstance(node, ast.Subscript):
            b = base_name(node.value)
            if b in LEVEL_VARS and isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
                out.append((node.lineno, b, node.slice.value, "subscript"))
        # X.get("key")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "get":
            b = base_name(node.func.value)
            if b in LEVEL_VARS and node.args and isinstance(node.args[0], ast.Constant) \
                    and isinstance(node.args[0].value, str):
                out.append((node.lineno, b, node.args[0].value, "get"))
    return out


def load(name):
    return json.loads((ROOT / "data" / "levels" / f"{name}.json").read_text(encoding="utf-8"))


records = []
for d in SRC_DIRS:
    for p in sorted((ROOT / d).rglob("*.py")):
        if "__pycache__" in p.parts:
            continue
        for lineno, var, key, kind in scan(p):
            records.append((str(p.relative_to(ROOT)), lineno, var, key, kind))

print("=" * 100)
print("ALL level-data key reads found by AST scan")
byfile = {}
for f, l, v, k, kind in records:
    byfile.setdefault((f, v), []).append((l, k, kind))
for (f, v), items in sorted(byfile.items()):
    keys = sorted({k for _, k, _ in items})
    print(f"\n{f}  [var: {v}]")
    for l, k, kind in sorted(items):
        print(f"    {f}:{l:<4d} {kind:9s} {v}[{k!r}]")

print("=" * 100)
print("CROSS-CHECK vs JSON")
WORLD = ["mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune"]
CAMPAIGN = ["level1", "level2", "level3", "level4", "tutorial"]


def check(level_names, var_names, nested):
    for name in level_names:
        cfg = load(name)
        target = cfg
        for n in nested:
            target = target.get(n, {}) if isinstance(target, dict) else {}
        missing = []
        for f, l, v, k, kind in records:
            if v not in var_names:
                continue
            if f.startswith("scenes/level") and not name.startswith("level"):
                continue
            if f.startswith("scenes/world_level") and name not in WORLD:
                continue
            if f.startswith("scenes/tutorial") and name != "tutorial":
                continue
            if k not in target:
                missing.append((f, l, v, k, kind))
        if missing:
            print(f"\n  {name}.json missing:")
            for f, l, v, k, kind in sorted(set(missing)):
                print(f"      {f}:{l}  {v}.{k!r}")


print("\n-- world levels: self.params / self.cfg / self.theme (top level of cfg) --")
check(WORLD, {"self.params", "self.cfg"}, [])
print("\n-- world levels: theme sub-dict --")
check(WORLD, {"self.theme"}, ["params", "theme"])
print("\n-- world levels: moment sub-dict --")
check(WORLD, {"self.moment_cfg"}, ["params", "moment"])
print("\n-- campaign levels: self.params / self.cfg --")
check(CAMPAIGN, {"self.params", "self.cfg"}, [])
