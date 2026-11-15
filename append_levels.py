import sys
with open('core/levels.py', 'r') as f:
    content = f.read()
new_func = '\n\ndef previous_mission(planet_id: str) -> str | None:\n    """Get the previous mission planet id in the world order.\n    Returns None for the first planet (tutorial).\n    """\n    order = ("mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune")\n    if planet_id in order:\n        idx = order.index(planet_id)\n        if idx > 0:\n            return order[idx - 1]\n    return None\n'
with open('core/levels.py', 'w') as f:
    f.write(content + new_func)
print('Added previous_mission function')