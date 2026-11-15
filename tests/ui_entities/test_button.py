"""ui/button.py - Button widget."""

from __future__ import annotations

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, r"E:\nasa")

import pygame

from conftest import key_down, mouse_down, mouse_motion, mouse_up
from core import audio, settings
from ui.button import Button


# --- construction -----------------------------------------------------------
def test_button_construction_defaults():
    b = Button((10, 20, 120, 40), "Go")
    assert b.rect == pygame.Rect(10, 20, 120, 40)
    assert b.label == "Go"
    assert b.on_click is None
    assert b.enabled is True
    assert b.hovered is False
    assert b.focused is False
    assert b.style == "primary"
    assert b.size == 22
    assert b.display is False
    assert b.subtitle is None
    assert b.align == "center"


def test_button_negative_rect_is_kept_raw():
    """pygame.Rect keeps negative width/height - the button becomes unusable."""
    b = Button((100, 100, -40, -20), "Neg")
    assert b.rect.width == -40 and b.rect.height == -20
    # must not crash when drawn
    b.draw(pygame.Surface((200, 200)))


# --- hover state ------------------------------------------------------------
def test_hover_sets_hovered_flag():
    b = Button((0, 0, 100, 50), "Hover")
    b.handle_events([mouse_motion((50, 25))])
    assert b.hovered is True
    b.handle_events([mouse_motion((500, 400))])
    assert b.hovered is False


def test_hover_sound_plays_only_on_entry(monkeypatch):
    calls = []
    monkeypatch.setattr(audio, "play", lambda name, gain=1.0: calls.append((name, gain)))
    b = Button((0, 0, 100, 50), "Hover")
    b.handle_events([mouse_motion((10, 10))])
    b.handle_events([mouse_motion((20, 20))])
    assert calls == [("hover", 0.6)], calls
    b.handle_events([mouse_motion((900, 900))])
    b.handle_events([mouse_motion((20, 20))])
    assert calls == [("hover", 0.6), ("hover", 0.6)], calls


def test_disabled_button_does_not_play_hover_sound(monkeypatch):
    calls = []
    monkeypatch.setattr(audio, "play", lambda name, gain=1.0: calls.append(name))
    b = Button((0, 0, 100, 50), "Hover", enabled=False)
    b.handle_events([mouse_motion((10, 10))])
    assert calls == [], calls


# --- click detection --------------------------------------------------------
def test_click_inside_calls_callback(monkeypatch):
    calls = []
    monkeypatch.setattr(audio, "play", lambda name, gain=1.0: None)
    b = Button((0, 0, 100, 50), "Go", lambda: calls.append(1))
    assert b.handle_events([mouse_down((50, 25))]) is True
    assert calls == [1]


def test_click_outside_does_not_call_callback(monkeypatch):
    calls = []
    monkeypatch.setattr(audio, "play", lambda name, gain=1.0: None)
    b = Button((0, 0, 100, 50), "Go", lambda: calls.append(1))
    assert b.handle_events([mouse_down((500, 400))]) is False
    assert calls == []


def test_click_on_edge_is_outside():
    """pygame rects are half-open: the right/bottom edge is outside."""
    calls = []
    b = Button((10, 10, 100, 50), "Go", lambda: calls.append(1))
    assert b.handle_events([mouse_down((109, 59))]) is True
    assert calls == [1]
    calls.clear()
    assert b.handle_events([mouse_down((110, 60))]) is False
    assert calls == []


def test_right_click_does_not_trigger():
    calls = []
    b = Button((0, 0, 100, 50), "Go", lambda: calls.append(1))
    assert b.handle_events([mouse_down((50, 25), button=3)]) is False
    assert calls == []


def test_activate_respects_enabled(monkeypatch):
    monkeypatch.setattr(audio, "play", lambda name, gain=1.0: None)
    calls = []
    b = Button((0, 0, 100, 50), "Go", lambda: calls.append(1), enabled=False)
    b.activate()
    assert calls == []
    b.enabled = True
    b.activate()
    assert calls == [1]


def test_activate_without_callback_is_safe(monkeypatch):
    monkeypatch.setattr(audio, "play", lambda name, gain=1.0: None)
    Button((0, 0, 10, 10), "x").activate()  # must not raise


# --- drawing ----------------------------------------------------------------
def test_draw_hovered_looks_different_from_unhovered(screen):
    b = Button((100, 100, 200, 60), "MOVE")
    screen.fill((0, 0, 0))
    b.draw(screen)
    plain = pygame.image.tostring(screen, "RGB")

    b.hovered = True
    screen.fill((0, 0, 0))
    b.draw(screen)
    hovered = pygame.image.tostring(screen, "RGB")
    assert plain != hovered, "hovered button must render differently"


def test_draw_focused_looks_active(screen):
    b = Button((100, 100, 200, 60), "MOVE")
    b.focused = True
    screen.fill((0, 0, 0))
    b.draw(screen)
    focused = pygame.image.tostring(screen, "RGB")
    b.focused = False
    screen.fill((0, 0, 0))
    b.draw(screen)
    plain = pygame.image.tostring(screen, "RGB")
    assert focused != plain


def test_draw_renders_the_label(screen):
    b = Button((100, 100, 220, 60), "LAUNCH")
    screen.fill((0, 0, 0))
    b.draw(screen)
    pixels = pygame.surfarray.array3d(screen)
    non_black = int((pixels.sum(axis=2) > 30).sum())
    assert non_black > 100, "label/button must put pixels on the surface"


def test_draw_all_styles(screen):
    for style in ("primary", "danger", "ghost", "unknown-style"):
        b = Button((50, 50, 200, 50), "Style", style=style)
        b.draw(screen)


def test_draw_disabled_button(screen):
    b = Button((50, 50, 200, 50), "Style", enabled=False)
    b.draw(screen)


def test_draw_zero_size_rect_does_not_crash(screen):
    b = Button((50, 50, 0, 0), "Zero")
    b.draw(screen)


def test_draw_subtitle(screen):
    b = Button((50, 50, 220, 60), "Main", subtitle="sub text")
    b.draw(screen)


def test_draw_display_font(screen):
    b = Button((50, 50, 220, 60), "DISPLAY", display=True)
    b.draw(screen)


# --- align ------------------------------------------------------------------
def _text_pixels(surface, rect):
    """Count non-background pixels inside ``rect``."""
    sub = surface.subsurface(rect).copy()
    arr = pygame.surfarray.array3d(sub)
    return int((arr.sum(axis=2) > 60).sum())


def _first_dark_column(surface, x_from, x_to, y):
    """First column at height ``y`` that holds a dark (text) pixel."""
    for x in range(x_from, x_to):
        r, g, b, *_ = surface.get_at((x, y))
        if r + g + b < 200:
            return x
    return None


def test_align_left_places_label_at_the_left_edge(screen):
    """`align="left"` must left-align the label at rect.x + 20."""
    from core import text as text_mod

    b = Button((100, 100, 300, 60), "LEFTALIGN", align="left")
    screen.fill((255, 255, 255))  # white so the label is visible outside the button
    b.draw(screen)
    width = text_mod.measure("LEFTALIGN", 22)[0]
    first = _first_dark_column(screen, 60, 460, 130)
    assert first is not None, "no label pixels found"
    assert first == 120, (
        "align='left' is not left-aligned: label starts at x=%s, expected x=120 "
        "(rect.x + 20). label width=%s -> centred would start at %s"
        % (first, width, 120 - width // 2)
    )


def test_align_center_places_label_in_the_middle(screen):
    from core import text as text_mod

    b = Button((100, 100, 300, 60), "CENTERED", align="center")
    screen.fill((255, 255, 255))
    b.draw(screen)
    width = text_mod.measure("CENTERED", 22)[0]
    first = _first_dark_column(screen, 60, 460, 130)
    assert first is not None, "no label pixels found"
    expected = 250 - width // 2
    assert abs(first - expected) <= 2, (
        f"align='center' label starts at x={first}, expected ~{expected}"
    )
