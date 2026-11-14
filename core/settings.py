"""Global constants and paths.

Nothing in here mutates at runtime; scenes and systems read from it.
"""

from pathlib import Path

# --- window -----------------------------------------------------------------
WIDTH = 1280
HEIGHT = 720
FPS = 60

TITLE = "HOMEBOUND"
SUBTITLE = "A Solar System Repair Mission"
CAPTION = f"{TITLE} - {SUBTITLE}"

# --- paths ------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
DATA = ROOT / "data"
SAVE_FILE = ROOT / "savegame.json"

FONT_DISPLAY = "PressStart2P-Regular.ttf"
FONT_BODY = "VT323-Regular.ttf"

# --- palette ----------------------------------------------------------------
SPACE = (5, 9, 20)
SPACE_DEEP = (2, 4, 10)
PANEL = (13, 23, 48)
PANEL_LIGHT = (20, 34, 68)
PANEL_EDGE = (36, 58, 102)
INK = (232, 241, 255)
DIM = (143, 163, 200)
FAINT = (72, 88, 118)
ACCENT = (94, 230, 208)
ACCENT_DARK = (22, 84, 82)
WARN = (255, 179, 71)
DANGER = (255, 92, 122)
GOLD = (255, 209, 102)
GREEN = (124, 224, 150)

DIFFICULTIES = ("easy", "normal", "hard")
DIFFICULTY_LABELS = {"easy": "Easy", "normal": "Normal", "hard": "Hard"}
DIFFICULTY_BLURB = {
    "easy": "5 hearts, slower hazards, +25% time, frequent hints",
    "normal": "3 hearts, standard hazards, standard time",
    "hard": "2 hearts, faster hazards, -15% time, hints on request only",
}

# --- scene names ------------------------------------------------------------
BOOT = "boot"
MENU = "menu"
MAP = "map"
TUTORIAL = "tutorial"
MARS = "mars"
MERCURY = "mercury"
VENUS = "venus"
ENDING = "ending"
PAUSE = "pause"

PLAYABLE_SCENES = (TUTORIAL, MARS, MERCURY, VENUS, ENDING)
