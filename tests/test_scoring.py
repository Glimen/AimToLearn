"""Tests du calcul des scores et du tableau des meilleurs scores."""

import math
import unittest

from game.highscores import insert_score, qualifies
from game.scoring import LevelStats, Session, compute_level_score, throughput


class ThroughputTest(unittest.TestCase):
    """Verifie la formule de Fitts."""

    def test_known_value(self) -> None:
        # D/W = 3 -> ID = log2(4) = 2 bits, en 1 s -> 2 bits/s
        self.assertAlmostEqual(throughput(300, 100, 1.0), 2.0)

    def test_zero_time_or_width(self) -> None:
        self.assertEqual(throughput(300, 100, 0.0), 0.0)
        self.assertEqual(throughput(300, 0, 1.0), 0.0)


class LevelScoreTest(unittest.TestCase):
    """Verifie les ratios et la regle de passage."""

    def test_perfect_level(self) -> None:
        stats = LevelStats(total_targets=15, clicks=15, clicks_on_target=15, hits=15)
        stats.samples = [(700, 100, 1.0)] * 15  # log2(8) = 3 bits/s = reference
        score = compute_level_score(stats, reference_throughput=3.0)
        self.assertAlmostEqual(score.precision, 1.0)
        self.assertAlmostEqual(score.completion, 1.0)
        self.assertAlmostEqual(score.speed, 1.0)
        self.assertAlmostEqual(score.global_score, 1.0)
        self.assertTrue(score.passed)

    def test_speed_is_capped(self) -> None:
        stats = LevelStats(total_targets=1, clicks=1, clicks_on_target=1, hits=1)
        stats.samples = [(700, 100, 0.1)]  # 30 bits/s
        self.assertEqual(compute_level_score(stats, reference_throughput=3.0).speed, 1.0)

    def test_no_click_no_crash(self) -> None:
        score = compute_level_score(LevelStats(total_targets=15, missed=15))
        self.assertEqual(score.precision, 0.0)
        self.assertEqual(score.speed, 0.0)
        self.assertFalse(score.passed)

    def test_threshold_is_strict(self) -> None:
        # precision 1 (0.4) + completion 1/3 (0.1) + vitesse 0 = 0.5 pile -> pas assez
        stats = LevelStats(total_targets=3, clicks=1, clicks_on_target=1, hits=1)
        stats.samples = [(0, 100, 1.0)]  # distance nulle -> 0 bit
        score = compute_level_score(stats)
        self.assertTrue(math.isclose(score.global_score, 0.5))
        self.assertFalse(score.passed)


class SessionTest(unittest.TestCase):
    """Verifie l'agregation des niveaux."""

    def test_summary_uses_last_attempt(self) -> None:
        bad = compute_level_score(LevelStats(total_targets=10, clicks=10, clicks_on_target=0, missed=10))
        good_stats = LevelStats(total_targets=10, clicks=10, clicks_on_target=10, hits=10)
        good = compute_level_score(good_stats)
        session = Session()
        session.record(0, bad)
        session.record(0, good)  # nouvel essai du meme niveau : remplace le precedent
        summary = session.summary()
        self.assertEqual(summary.levels_played, 1)
        self.assertEqual(summary.levels_passed, 1)
        self.assertAlmostEqual(summary.precision, 1.0)
        self.assertEqual(summary.points, round(good.global_score * 100))

    def test_only_full_game_is_ranked(self) -> None:
        self.assertTrue(Session().ranked)
        self.assertFalse(Session(start_level=3).ranked)

    def test_empty_session(self) -> None:
        summary = Session().summary()
        self.assertEqual(summary.points, 0)
        self.assertEqual(summary.levels_played, 0)


class HighscoresTest(unittest.TestCase):
    """Verifie le classement."""

    def test_insert_sorted_and_truncated(self) -> None:
        entries = [{"name": n, "points": p, "levels": 1} for n, p in [("a", 300), ("b", 100), ("c", 200)]]
        ranked, index = insert_score(entries, "new", 250, 2, size=3)
        self.assertEqual([e["name"] for e in ranked], ["a", "new", "c"])
        self.assertEqual(index, 1)

    def test_tie_keeps_older_first(self) -> None:
        entries = [{"name": "old", "points": 100, "levels": 1}]
        ranked, index = insert_score(entries, "new", 100, 1)
        self.assertEqual([e["name"] for e in ranked], ["old", "new"])
        self.assertEqual(index, 1)

    def test_not_ranked(self) -> None:
        entries = [{"name": "a", "points": 100, "levels": 1}]
        _, index = insert_score(entries, "new", 50, 1, size=1)
        self.assertIsNone(index)

    def test_qualifies(self) -> None:
        full = [{"name": "a", "points": 100, "levels": 1}] * 3
        self.assertTrue(qualifies([], 0, size=3))
        self.assertFalse(qualifies(full, 100, size=3))
        self.assertTrue(qualifies(full, 101, size=3))


if __name__ == "__main__":
    unittest.main()
