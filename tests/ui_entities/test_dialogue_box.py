"""ui/dialogue_box.py - Laika's dialogue box."""

from __future__ import annotations

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, r"E:\nasa")

import pygame

from conftest import key_down, mouse_down
from core import audio, settings
from ui.dialogue_box import ADVANCE_KEYS, DialogueBox


def make_box(game, rect=None):
    return DialogueBox(game, rect)


# --- construction -----------------------------------------------------------
def test_construction_defaults(game):
    box = make_box(game)
    assert box.active is False
    assert box.lines == []
    assert box.index == 0
    assert box.revealed == 0.0
    assert box.speaker == "Laika"
    assert box.chars_per_second == 62.0
    assert box.is_hint is False
    assert box.rect.width == settings.WIDTH - 208
    assert box.rect.height == 170


def test_construction_with_custom_rect(game):
    box = make_box(game, (10, 20, 300, 120))
    assert box.rect == pygame.Rect(10, 20, 300, 120)


# --- queue ------------------------------------------------------------------
def test_queue_plain_strings(game):
    box = make_box(game)
    box.queue(["Hello there", "Second line"])
    assert box.active is True
    assert len(box.lines) == 2
    assert box.current_text == "Hello there"
    assert box.current_line["speaker"] == "Laika"


def test_queue_dict_lines_with_speakers(game):
    box = make_box(game)
    box.queue(
        [
            {"text": "Systems nominal", "speaker": "System"},
            {"text": "Copy that", "speaker": "Mission Control"},
        ]
    )
    assert box.current_line["speaker"] == "System"
    box.advance()  # reveal
    box.advance()  # next line
    assert box.current_line["speaker"] == "Mission Control"


def test_queue_strips_whitespace(game):
    box = make_box(game)
    box.queue(["   padded   "])
    assert box.current_text == "padded"


def test_queue_empty_list_calls_on_done_immediately(game):
    box = make_box(game)
    calls = []
    box.queue([], on_done=lambda: calls.append(1))
    assert calls == [1]
    assert box.active is False


def test_queue_of_blank_strings_calls_on_done(game):
    box = make_box(game)
    calls = []
    box.queue(["", "   "], on_done=lambda: calls.append(1))
    assert calls == [1]
    assert box.active is False


def test_queue_empty_while_active_keeps_old_dialogue_alive(game):
    """Bug probe: queueing nothing while a dialogue is running.

    ``queue([])`` fires the new ``on_done`` immediately but leaves the *old*
    lines on screen with ``active`` still True, so the player is stuck in a
    dialogue whose callback can fire twice.
    """
    box = make_box(game)
    old_calls = []
    box.queue(["Original line"], on_done=lambda: old_calls.append(1))
    calls = []
    box.queue([], on_done=lambda: calls.append(1))
    assert calls == [1], "new on_done fired"
    assert box.active is False, (
        "queue([]) left the stale dialogue active: the player is stuck"
    )
    # and the stale callback must not fire a second time
    box.advance()
    box.advance()
    assert old_calls == [], "the previous on_done fired again"


def test_queue_resets_index_and_reveal(game):
    box = make_box(game)
    box.queue(["One", "Two"])
    box.update(1.0)
    box.advance()
    assert box.index == 1
    assert box.revealed == 0.0


def test_queue_sets_default_speaker(game):
    box = make_box(game)
    box.queue(["Hi"], speaker="Mission Control")
    assert box.default_speaker == "Mission Control"


def test_show_single_line(game):
    box = make_box(game)
    box.show("Only line", "Laika")
    assert box.active is True
    assert len(box.lines) == 1
    assert box.current_text == "Only line"


def test_hint_uses_gold_accent(game):
    box = make_box(game)
    box.hint("Try the beacon")
    assert box.is_hint is True
    assert box.accent == settings.GOLD


# --- typewriter -------------------------------------------------------------
def test_typewriter_reveals_progressively(game):
    box = make_box(game)
    box.queue(["0123456789"])
    box.update(0.1)  # 62 chars/s -> 6.2 chars
    assert 0 < box.revealed < 10
    assert box.fully_revealed is False
    box.update(10.0)
    assert box.revealed == 10.0
    assert box.fully_revealed is True


def test_typewriter_never_exceeds_the_text_length(game):
    box = make_box(game)
    box.queue(["short"])
    box.update(1000.0)
    assert box.revealed == 5.0


def test_update_with_zero_dt(game):
    box = make_box(game)
    box.queue(["abcdef"])
    box.update(0.0)
    assert box.revealed == 0.0
    assert box.fully_revealed is False


def test_update_with_huge_dt(game):
    box = make_box(game)
    box.queue(["abcdef"])
    box.update(1e9)
    assert box.revealed == 6.0


def test_update_when_inactive_is_a_noop(game):
    box = make_box(game)
    box.update(5.0)
    assert box.revealed == 0.0


# --- advance ----------------------------------------------------------------
def test_advance_reveals_all_first(game):
    box = make_box(game)
    box.queue(["abcdefghij"])
    box.advance()
    assert box.revealed == 10.0
    assert box.index == 0


def test_advance_moves_to_the_next_line(game):
    box = make_box(game)
    box.queue(["first", "second"])
    box.advance()  # reveal
    box.advance()  # next line
    assert box.index == 1
    assert box.current_text == "second"
    assert box.revealed == 0.0


def test_advance_at_the_end_fires_on_done(game):
    box = make_box(game)
    calls = []
    box.queue(["only"], on_done=lambda: calls.append(1))
    box.advance()
    box.advance()
    assert calls == [1]
    assert box.active is False
    assert box.lines == []


def test_advance_when_inactive_is_a_noop(game):
    box = make_box(game)
    box.advance()
    assert box.index == 0


def test_clear_resets_state(game):
    box = make_box(game)
    box.queue(["a", "b"])
    box.clear()
    assert box.active is False
    assert box.lines == []
    assert box.index == 0
    assert box.revealed == 0.0
    assert box.on_done is None


# --- input ------------------------------------------------------------------
def test_space_advances(game):
    box = make_box(game)
    box.queue(["one", "two"])
    box.handle_events([key_down(pygame.K_SPACE)])
    assert box.fully_revealed is True


def test_e_advances(game):
    box = make_box(game)
    box.queue(["one", "two"])
    box.handle_events([key_down(pygame.K_e)])
    assert box.fully_revealed is True


def test_return_advances(game):
    box = make_box(game)
    box.queue(["one", "two"])
    box.handle_events([key_down(pygame.K_RETURN)])
    assert box.fully_revealed is True


def test_mouse_click_advances(game):
    box = make_box(game)
    box.queue(["one", "two"])
    box.handle_events([mouse_down((640, 600))])
    assert box.fully_revealed is True


def test_escape_also_advances(game):
    box = make_box(game)
    box.queue(["one", "two"])
    box.handle_events([key_down(pygame.K_ESCAPE)])
    assert box.fully_revealed is True


def test_handle_events_when_inactive_returns_false(game):
    box = make_box(game)
    assert box.handle_events([key_down(pygame.K_SPACE)]) is False


def test_advance_keys_constant_includes_space_and_e():
    assert pygame.K_SPACE in ADVANCE_KEYS
    assert pygame.K_e in ADVANCE_KEYS


# --- properties -------------------------------------------------------------
def test_current_line_out_of_range_returns_placeholder(game):
    box = make_box(game)
    box.lines = [{"text": "x", "speaker": "Laika"}]
    box.index = 5
    assert box.current_line["text"] == ""
    assert box.current_line["speaker"] == "Laika"


def test_is_active_reflects_state(game):
    box = make_box(game)
    assert box.is_active() is False
    box.queue(["x"])
    assert box.is_active() is True


# --- drawing ----------------------------------------------------------------
def test_draw_does_not_crash(game, screen):
    box = make_box(game)
    box.draw(screen)  # inactive -> no-op


def test_draw_renders_the_line(game, screen):
    box = make_box(game)
    box.queue(["Laika speaking loudly"])
    box.update(5.0)
    screen.fill((0, 0, 0))
    box.draw(screen)
    arr = pygame.surfarray.array3d(screen)
    assert int((arr.sum(axis=2) > 60).sum()) > 500


def test_draw_with_long_text_wraps_inside_the_panel(game, screen):
    box = make_box(game)
    long_text = " ".join(["Mars"] * 200)
    box.queue([long_text])
    box.update(100.0)
    screen.fill((0, 0, 0))
    box.draw(screen)
    # nothing may be drawn past the right edge of the dialogue panel
    arr = pygame.surfarray.array3d(screen)
    right = arr[:, box.rect.right + 1:, :].sum(axis=2)
    assert int((right > 30).sum()) == 0, "text leaked past the panel edge"


def test_draw_empty_text_is_safe(game, screen):
    box = make_box(game)
    box.queue(["x"])
    box.lines = [{"text": "", "speaker": "Laika"}]
    box.draw(screen)


def test_draw_speaker_badge_for_non_laika(game, screen):
    box = make_box(game)
    box.queue([{"text": "Systems go", "speaker": "Mission Control"}])
    box.update(1.0)
    screen.fill((0, 0, 0))
    box.draw(screen)


def test_draw_hint_badge(game, screen):
    box = make_box(game)
    box.hint("Try the beacon")
    box.update(1.0)
    screen.fill((0, 0, 0))
    box.draw(screen)


def test_draw_at_a_tiny_size(game, screen):
    box = make_box(game, (0, 0, 80, 40))
    box.queue(["x"])
    box.update(1.0)
    box.draw(screen)


def test_hint_accent_is_reset_when_advancing(game):
    box = make_box(game)
    box.hint("hint one")
    box.update(1.0)
    box.advance()  # reveal
    box.advance()  # next line (empty -> finishes)
    assert box.accent in (settings.GOLD, settings.ACCENT)


def test_hint_accent_lost_after_advance(game):
    """Bug probe: a hint keeps the HINT badge but loses the gold accent."""
    box = make_box(game)
    box.hint("first hint")
    box.update(5.0)
    gold = box.accent
    box.queue(["second line"], accent=settings.GOLD, hint=True)
    box.update(5.0)
    assert box.accent == settings.GOLD
    box.advance()  # reveal
    box.advance()  # next line
    assert box.is_hint is True
    assert box.accent == gold, (
        "hint accent changed while is_hint is still True "
        f"({gold} -> {box.accent})"
    )
