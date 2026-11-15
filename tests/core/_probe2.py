"""Scratch exploration probe 2 (not a test)."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import sys
sys.path.insert(0, r"E:\nasa")

import json, tempfile, pathlib
from core import levels, settings, save, color, camera, world_gen, science, assets, text, audio, weather

print("=== levels errors ===")
for fn, arg in [(levels.load_level, "nope"), (levels.level_meta, "nope")]:
    try:
        fn(arg)
    except Exception as e:
        print(" ", fn.__name__, type(e).__name__, e)

print("load_level('mars') keys:", list(levels.load_level("mars").keys()))
print("load_level('tutorial'):", json.dumps(levels.load_level("tutorial"), indent=1)[:400])
print("params_for difficulty:", levels.params_for({"params": {"a": 1, "difficulty": {"hard": {"a": 9}}}}, "hard"))
print("params_for bad diff:", levels.params_for({"params": {"a": 1}}, "insane"))
print("params_for no params:", levels.params_for({}, "easy"))
print("params_for params None:", levels.params_for({"params": None}, "easy"))
print("params_for difficulty not dict:", end=" ")
try:
    print(levels.params_for({"params": {"difficulty": 5}}, "easy"))
except Exception as e:
    print(type(e).__name__, e)

print("load_dialogue('dialogue/mars.json') triggers:", levels.load_dialogue("dialogue/mars.json")["triggers"])
print("load_dialogue('mars.json'):", levels.load_dialogue("mars.json")["triggers"])
try:
    levels.load_dialogue("missing.json")
except Exception as e:
    print("  missing dialogue ->", type(e).__name__, e)

print("load_planets order:", levels.load_planets()["order"])
print("planet_index len:", len(levels.planet_index()))
print("level_names:", levels.level_names())
print("level_list len:", len(levels.level_list()))
print("level_ids:", levels.level_ids())

print("=== save ===")
print("VERSION", save.VERSION, "path", save._path())
print("exists:", save.exists())
print("read (real file):", type(save.read()))
tmp = pathlib.Path(tempfile.mkdtemp())
settings.SAVE_FILE = tmp / "s.json"
print("exists after redirect:", save.exists())
print("read missing:", save.read())
print("write:", save.write({"a": 1}))
print("read:", save.read())
(tmp / "s.json").write_text("{not json", encoding="utf-8")
print("read corrupt:", save.read())
(tmp / "s.json").write_text("[1,2]", encoding="utf-8")
print("read list:", save.read())
settings.SAVE_FILE = tmp / "nodir" / "deep" / "s.json"
print("write into missing dir:", save.write({"a": 1}))
save.clear()
print("clear ok")

print("=== color ===")
print(color.hex_to_rgb("#ff8800"), color.hex_to_rgb("f80"), color.hex_to_rgb("zzz"), color.hex_to_rgb(""))
print(color.hex_to_rgb("12345"), color.hex_to_rgb("#12345g"))
print(color.mix((0,0,0),(255,255,255),0.5), color.mix((0,0,0),(255,255,255),-5), color.mix((0,0,0),(255,255,255),5))
print(color.scale((100,200,300), 2.0))
print(color.blend_over((255,0,0),(0,0,255),0.5))
try:
    print(color.mix((1,2),(3,4),0.5))
except Exception as e:
    print("mix mismatched ->", type(e).__name__, e)

print("=== camera ===")
import pygame
pygame.init()
c = camera.Camera(5000, 1000)
print("clamp(-100,-100):", c.clamp(-100,-100), "clamp(99999,99999):", c.clamp(99999,99999))
c.snap((1000, 500)); print("snap:", c.offset)
c.follow((2000, 500), 0.1); print("follow:", c.offset)
print("to_screen:", c.to_screen((1000,500)), "visible:", c.visible(pygame.Rect(0,0,10,10)))
c2 = camera.Camera(100, 100)  # smaller than view
print("small world clamp:", c2.clamp(50,50), c2.world_w, c2.view_w)
c3 = camera.Camera(2000, 900)
print("world_h 900 view 720 clamp y:", c3.clamp(0, 500))

print("=== science ===")
print("science.json exists:", (settings.DATA / "science.json").exists())
print("load keys:", list(science.load().keys()))
print("systems:", [s["id"] for s in science.systems()])
print("system('osdr'):", science.system("osdr") is not None, science.system("zzz"))
print("facts:", science.facts())
print("fact('x'):", science.fact("x"))
print("updated:", science.updated())
print("latest_event:", science.latest_event())

print("=== assets ===")
print("path('fonts','x.ttf'):", assets.path("fonts", "x.ttf"))
print("font(12):", assets.font(12))
print("font(1):", assets.font(1))
print("image('nope.png'):", assets.image("nope.png"))
print("portrait(64):", assets.portrait(64))
print("portrait(0):", assets.portrait(0))
print("image scale:", assets.image("nope.png", 2))

print("=== text ===")
text.set_scale(1.0)
print("get_scale", text.get_scale())
text.set_scale(99); print("clamped scale:", text.get_scale())
text.set_scale(0.1); print("clamped scale low:", text.get_scale())
text.set_scale(1.0)
surf = pygame.Surface((200, 100))
print("wrap:", text.wrap("hello world this is a long line of text", 12, 60))
print("measure:", text.measure("hi", 12))
r = text.draw(surf, "hi", (0,0)); print("draw rect:", r)
r2 = text.draw(surf, "hi", (100,50), center=True); print("center rect:", r2)
print("draw_centered:", text.draw_centered(surf, "hi", (100,50)))
print("wrap empty:", text.wrap("", 12, 100))
print("wrap newline:", text.wrap("a\n\nb", 12, 100))

print("=== audio ===")
audio.init()
print("get_volume:", audio.get_volume(), "is_muted:", audio.is_muted())
audio.play("click"); audio.play("nope")
audio.set_volume(5); print("vol clamped:", audio.get_volume())
audio.set_volume(-1); print("vol clamped low:", audio.get_volume())
audio.set_volume(0.8)
audio.set_muted(True); print("muted:", audio.is_muted())
audio.set_muted(False)

print("=== world_gen ===")
w = world_gen.generate("mars", {"seed": 11, "world_length": 5400, "ground_y": 560})
print("keys:", sorted(w.keys()))
print("platforms:", len(w["platforms"]), "hazards:", len(w["hazards"]), "enemies:", len(w["enemies"]))
print("part_pos", w["part_pos"], "exit_pos", w["exit_pos"], "world_w", w["world_w"])
w2 = world_gen.generate("mars", {"seed": 11, "world_length": 5400, "ground_y": 560})
print("deterministic:", w["platforms"] == w2["platforms"])
try:
    wt = world_gen.generate("t", {"seed": 1, "world_length": 100})
    print("tiny world ok:", len(wt["platforms"]), wt["part_pos"], wt["exit_pos"])
except Exception as e:
    print("tiny world ->", type(e).__name__, e)
try:
    wt = world_gen.generate("t", {"seed": 1, "world_length": 5000, "ground_y": 700})
    print("ground_y 700 ok:", len(wt["platforms"]))
except Exception as e:
    print("ground_y 700 ->", type(e).__name__, e)
try:
    wt = world_gen.generate("t", {"seed": 1, "world_length": 5000, "ground_y": 100})
    print("ground_y 100 ok:", len(wt["platforms"]))
except Exception as e:
    print("ground_y 100 ->", type(e).__name__, e)
print("default_theme:", world_gen.default_theme())

print("=== weather ===")
wth = weather.Weather({"type": "dust", "density": 20, "wind": [10, 5], "color": [1,2,3,4], "haze": [1,2,3,4]})
wth.update(0.016)
print("weather ok", len(wth.particles))
wth2 = weather.Weather(None)
print("none weather:", wth2.kind, wth2.particles)
wth3 = weather.Weather({"type": "acid_rain", "density": 10, "color": [255,0,0]})
wth3.update(0.016)
surf2 = pygame.Surface((settings.WIDTH, settings.HEIGHT))
wth3.draw(surf2)
print("rain draw ok")
