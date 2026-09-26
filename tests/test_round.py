"""Tests du deroulement d'un niveau (gestes, compteurs, fin de niveau)."""

import random
import unittest

from config.levels import (
    ALL_SHAPES,
    GESTURE_DOUBLE_CLICK,
    GESTURE_DRAG,
    GESTURE_RIGHT_CLICK,
    GESTURE_SCROLL,
    LevelConfig,
)
from game import round as rnd
from lib.geometry import Area

VIEWPORT = Area(0, 70, 1280, 650)
CORNER = (1, 71)  # position de depart du curseur


def make_round(total: int = 3, **level_args: object) -> rnd.LevelRound:
    """Cree un niveau demarre, avec un aleatoire reproductible."""
    level = LevelConfig(name="test", instruction="", **level_args)
    game_round = rnd.LevelRound(level, VIEWPORT, random.Random(42), total_targets=total)
    game_round.start(CORNER)
    return game_round


def target_screen_pos(game_round: rnd.LevelRound) -> tuple[float, float]:
    """Position ecran du centre de la cible courante."""
    return game_round.target.x, game_round.target.y - game_round.scroll_offset


def empty_spot(game_round: rnd.LevelRound) -> tuple[float, float]:
    """Un point de la zone de jeu loin de la cible (clic dans le vide)."""
    x = 50 if game_round.target.x > 640 else 1230
    return x, game_round.target.y


class ClickTest(unittest.TestCase):
    """Niveau clic simple."""

    def test_full_level(self) -> None:
        game_round = make_round(total=3)
        self.assertEqual(game_round.press(1, empty_spot(game_round)), rnd.MISS)
        for _ in range(3):
            game_round.update(0.5, CORNER)
            self.assertEqual(game_round.press(1, target_screen_pos(game_round)), rnd.HIT)
        self.assertTrue(game_round.finished)
        self.assertIsNone(game_round.target)
        stats = game_round.stats
        self.assertEqual((stats.clicks, stats.clicks_on_target, stats.hits), (4, 3, 3))
        self.assertEqual(len(stats.samples), 3)
        self.assertAlmostEqual(stats.samples[0][2], 0.5)

    def test_wrong_button(self) -> None:
        game_round = make_round()
        self.assertEqual(game_round.press(3, target_screen_pos(game_round)), rnd.WRONG_BUTTON)
        self.assertEqual(game_round.stats.clicks_on_target, 0)

    def test_click_in_hud_misses(self) -> None:
        game_round = make_round()
        self.assertEqual(game_round.press(1, (game_round.target.x, 10)), rnd.MISS)

    def test_new_target_far_from_cursor(self) -> None:
        game_round = make_round(total=20)
        for _ in range(19):
            pos = target_screen_pos(game_round)
            game_round.press(1, pos)
            dist = ((game_round.target.x - pos[0]) ** 2 + (game_round.target.y - pos[1]) ** 2) ** 0.5
            self.assertGreaterEqual(dist, 200)


class ExpireTest(unittest.TestCase):
    """Cibles a duree de vie limitee."""

    def test_expired_targets_count_as_missed(self) -> None:
        game_round = make_round(total=2, lifetime=1.0)
        self.assertEqual(game_round.update(0.5, CORNER), rnd.NONE)
        self.assertEqual(game_round.update(0.6, CORNER), rnd.EXPIRE)
        self.assertEqual(game_round.update(1.1, CORNER), rnd.EXPIRE)
        self.assertTrue(game_round.finished)
        self.assertEqual((game_round.stats.missed, game_round.stats.clicks), (2, 0))


class DoubleClickTest(unittest.TestCase):
    """Niveau double-clic."""

    def test_double_click(self) -> None:
        game_round = make_round(gesture=GESTURE_DOUBLE_CLICK)
        pos = target_screen_pos(game_round)
        self.assertEqual(game_round.press(1, pos), rnd.PROGRESS)
        game_round.update(0.2, CORNER)
        self.assertEqual(game_round.press(1, pos), rnd.HIT)
        self.assertEqual(game_round.stats.clicks_on_target, 2)

    def test_too_slow(self) -> None:
        game_round = make_round(gesture=GESTURE_DOUBLE_CLICK)
        pos = target_screen_pos(game_round)
        game_round.press(1, pos)
        game_round.update(0.5, CORNER)
        self.assertEqual(game_round.press(1, pos), rnd.PROGRESS)  # repart de zero


class RightClickTest(unittest.TestCase):
    """Niveau clic droit."""

    def test_right_click(self) -> None:
        game_round = make_round(gesture=GESTURE_RIGHT_CLICK)
        pos = target_screen_pos(game_round)
        self.assertEqual(game_round.press(1, pos), rnd.WRONG_BUTTON)
        self.assertEqual(game_round.press(3, pos), rnd.HIT)


class DecoyTest(unittest.TestCase):
    """Niveau avec leurres."""

    def test_decoys_have_other_shapes(self) -> None:
        game_round = make_round(shapes=ALL_SHAPES, decoys=3)
        self.assertEqual(len(game_round.decoys), 3)
        for decoy in game_round.decoys:
            self.assertNotEqual(decoy.shape, game_round.target.shape)
        decoy = game_round.decoys[0]
        self.assertEqual(game_round.press(1, (decoy.x, decoy.y)), rnd.DECOY)
        self.assertEqual(game_round.stats.clicks_on_target, 0)


class DragTest(unittest.TestCase):
    """Niveau glisser-deposer."""

    def test_drop_outside_then_inside(self) -> None:
        game_round = make_round(gesture=GESTURE_DRAG, size=70, zone_size=140)
        origin = target_screen_pos(game_round)
        zone = (game_round.drop_zone.x, game_round.drop_zone.y)
        self.assertEqual(game_round.press(1, origin), rnd.PROGRESS)
        game_round.motion((origin[0] + 10, origin[1]))
        self.assertEqual(game_round.release(1, (origin[0] + 10, origin[1])), rnd.DROP_MISS)
        self.assertEqual(target_screen_pos(game_round), origin)  # retour au depart
        game_round.press(1, origin)
        game_round.motion(zone)
        self.assertEqual(game_round.release(1, zone), rnd.HIT)
        self.assertEqual(game_round.stats.hits, 1)


class ScrollTest(unittest.TestCase):
    """Niveau molette."""

    def test_target_starts_hidden_and_scroll_reveals_it(self) -> None:
        game_round = make_round(gesture=GESTURE_SCROLL, size=80)
        self.assertNotEqual(game_round.target_direction, 0)
        for _ in range(200):
            if game_round.target_direction == 0:
                break
            game_round.wheel(-game_round.target_direction)  # cran vers le bas si cible en dessous
        self.assertEqual(game_round.target_direction, 0)
        self.assertEqual(game_round.press(1, target_screen_pos(game_round)), rnd.HIT)

    def test_scroll_is_clamped(self) -> None:
        game_round = make_round(gesture=GESTURE_SCROLL)
        game_round.wheel(10)  # vers le haut depuis le haut
        self.assertEqual(game_round.scroll_offset, 0.0)


if __name__ == "__main__":
    unittest.main()
