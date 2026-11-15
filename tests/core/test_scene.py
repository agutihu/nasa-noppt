"""Tests for ``core.scene`` - the Scene base class, SceneManager and Game."""

from __future__ import annotations

import sys

sys.path.insert(0, r"E:\nasa")

import pygame
import pytest

from core.game_state import GameState
from core.scene import Game, Scene, SceneManager


@pytest.fixture
def game():
    state = GameState()
    screen = pygame.Surface((1280, 720))
    window = pygame.Surface((1280, 720))
    return Game(screen, window, state)


class DummyScene(Scene):
    name = "dummy"
    counts_time = True

    def __init__(self, game):
        super().__init__(game)
        self.entered = 0
        self.exited = 0
        self.updates = 0
        self.drawn = 0
        self.events = []
        self.enter_data = {}

    def on_enter(self, **data):
        self.entered += 1
        self.enter_data = data

    def on_exit(self):
        self.exited += 1

    def handle_events(self, events):
        self.events.extend(events)

    def update(self, dt):
        self.updates += 1

    def draw(self, screen):
        self.drawn += 1


class TestSceneBase:
    def test_class_defaults(self):
        assert Scene.name == "scene"
        assert Scene.counts_time is False

    def test_init_captures_game_references(self, game):
        scene = Scene(game)
        assert scene.game is game
        assert scene.screen is game.screen
        assert scene.state is game.state
        assert scene.manager is game.manager

    def test_hooks_are_no_ops(self, game):
        scene = Scene(game)
        assert scene.on_enter() is None
        assert scene.on_exit() is None
        assert scene.handle_events([]) is None
        assert scene.update(0.016) is None
        assert scene.draw(game.screen) is None

    def test_on_enter_accepts_kwargs(self, game):
        class Kw(Scene):
            def __init__(self, game):
                super().__init__(game)
                self.kwargs = None

            def on_enter(self, **data):
                self.kwargs = data

        scene = Kw(game)
        scene.on_enter(a=1, b="two")
        assert scene.kwargs == {"a": 1, "b": "two"}


class TestSceneManager:
    def test_init(self, game):
        manager = game.manager
        assert isinstance(manager, SceneManager)
        assert manager.game is game
        assert manager.state is game.state
        assert manager.screen is game.screen
        assert manager.registry == {}
        assert manager.stack == []

    def test_register(self, game):
        game.manager.register("dummy", DummyScene)
        assert "dummy" in game.manager.registry

    def test_switch_creates_scene(self, game):
        game.manager.register("dummy", DummyScene)
        scene = game.manager.switch("dummy")
        assert isinstance(scene, DummyScene)
        assert game.manager.stack == [scene]
        assert game.manager.current is scene
        assert game.manager.current_name == "dummy"

    def test_switch_calls_on_enter(self, game):
        game.manager.register("dummy", DummyScene)
        scene = game.manager.switch("dummy")
        assert scene.entered == 1
        assert scene.enter_data == {}

    def test_switch_forwards_data(self, game):
        game.manager.register("dummy", DummyScene)
        scene = game.manager.switch("dummy", planet="mars", seed=3)
        assert scene.enter_data == {"planet": "mars", "seed": 3}

    def test_switch_unknown_raises_key_error(self, game):
        with pytest.raises(KeyError) as excinfo:
            game.manager.switch("nope")
        assert "nope" in str(excinfo.value)

    def test_switch_replaces_stack(self, game):
        game.manager.register("dummy", DummyScene)
        first = game.manager.switch("dummy")
        second = game.manager.switch("dummy")
        assert first.exited == 1
        assert game.manager.stack == [second]
        assert len(game.manager.stack) == 1

    def test_push_overlays(self, game):
        game.manager.register("dummy", DummyScene)
        base = game.manager.switch("dummy")
        overlay = game.manager.push("dummy")
        assert len(game.manager.stack) == 2
        assert game.manager.current is overlay
        assert base.entered == 1

    def test_pop_removes_top(self, game):
        game.manager.register("dummy", DummyScene)
        game.manager.switch("dummy")
        overlay = game.manager.push("dummy")
        game.manager.pop()
        assert game.manager.stack == [game.manager.stack[0]]
        assert overlay.exited == 1

    def test_pop_on_empty_stack_is_safe(self, game):
        game.manager.pop()  # must not raise
        assert game.manager.stack == []

    def test_pop_on_empty_stack_does_not_raise(self, game):
        assert game.manager.stack == []
        game.manager.pop()

    def test_current_is_none_when_empty(self, game):
        assert game.manager.current is None
        assert game.manager.current_name == ""

    def test_reload_replaces_the_scene(self, game):
        game.manager.register("dummy", DummyScene)
        first = game.manager.switch("dummy")
        second = game.manager.reload()
        assert second is not first
        assert first.exited == 1
        assert game.manager.current is second

    def test_reload_on_empty_stack_raises(self, game):
        with pytest.raises(RuntimeError):
            game.manager.reload()

    def test_handle_events_goes_to_top_scene(self, game):
        game.manager.register("dummy", DummyScene)
        game.manager.switch("dummy")
        top = game.manager.push("dummy")
        event = pygame.event.Event(pygame.USEREVENT, {"x": 1})
        game.manager.handle_events([event])
        assert top.events == [event]

    def test_handle_events_with_empty_stack(self, game):
        game.manager.handle_events([])  # must not raise

    def test_update_only_updates_the_top_scene(self, game):
        game.manager.register("dummy", DummyScene)
        base = game.manager.switch("dummy")
        top = game.manager.push("dummy")
        game.manager.update(0.5)
        assert top.updates == 1
        assert base.updates == 0

    def test_update_with_empty_stack(self, game):
        game.manager.update(0.5)  # must not raise

    def test_elapsed_only_counts_when_counts_time(self, game):
        game.manager.register("dummy", DummyScene)
        game.manager.switch("dummy")
        game.manager.update(0.5)
        assert game.state.elapsed == pytest.approx(0.5)

    def test_elapsed_not_counted_without_counts_time(self, game):
        class NoTime(DummyScene):
            counts_time = False

        game.manager.register("notime", NoTime)
        game.manager.switch("notime")
        game.manager.update(0.5)
        assert game.state.elapsed == 0.0

    def test_draw_draws_every_scene_in_the_stack(self, game):
        game.manager.register("dummy", DummyScene)
        base = game.manager.switch("dummy")
        top = game.manager.push("dummy")
        game.manager.draw()
        assert base.drawn == 1
        assert top.drawn == 1

    def test_draw_with_empty_stack(self, game):
        game.manager.draw()  # must not raise

    def test_assert_name_fills_in_a_missing_name(self, game):
        class Nameless(Scene):
            name = ""

        game.manager.register("x", Nameless)
        scene = game.manager.switch("x")
        assert scene.name == "x"


class TestGame:
    def test_attributes(self, game):
        assert game.running is True
        assert game.screen is not None
        assert game.window is not None
        assert game.state is not None
        assert isinstance(game.manager, SceneManager)

    def test_quit(self, game):
        game.quit()
        assert game.running is False

    def test_scale_mouse_identity_at_native_size(self, game):
        assert game.scale_mouse((640, 360)) == (640, 360)

    def test_scale_mouse_top_left(self, game):
        assert game.scale_mouse((0, 0)) == (0, 0)

    def test_scale_mouse_handles_negative_coordinates(self, game):
        x, y = game.scale_mouse((-100, -50))
        assert x < 0 and y < 0

    def test_scale_mouse_zero_sized_window(self, game):
        game.window = pygame.Surface((0, 0))
        assert game.scale_mouse((10, 10)) == (0, 0)

    def test_scale_mouse_letterboxes(self, game):
        # 2560x720 window -> scale 1.0, canvas centred vertically (no letterbox),
        # horizontally there is extra room so the canvas is centred.
        game.window = pygame.Surface((2560, 720))
        x, y = game.scale_mouse((1280, 360))
        assert y == 360
        assert x == 640
