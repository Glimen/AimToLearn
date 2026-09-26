"""Tests du deblocage des niveaux et de la sauvegarde de la progression."""

import tempfile
import unittest
from pathlib import Path
from unittest import mock

import lib.storage as storage
from game.progress import unlock_after


class UnlockAfterTest(unittest.TestCase):
    """Verifie la regle de deblocage."""

    def test_pass_unlocks_next(self) -> None:
        self.assertEqual(unlock_after(0, 0, True, 11), 1)

    def test_fail_changes_nothing(self) -> None:
        self.assertEqual(unlock_after(3, 3, False, 11), 3)

    def test_never_goes_back(self) -> None:
        # Rejouer et reussir un niveau ancien ne fait pas perdre les suivants
        self.assertEqual(unlock_after(7, 2, True, 11), 7)

    def test_last_level_stays_in_range(self) -> None:
        self.assertEqual(unlock_after(10, 10, True, 11), 10)


class ProgressStorageTest(unittest.TestCase):
    """Verifie la sauvegarde sur disque (dossier temporaire)."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.data_dir = Path(self._tmp.name)
        patcher = mock.patch.object(storage, "DATA_DIR", self.data_dir)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self._tmp.cleanup)

    def test_missing_file_means_level_one(self) -> None:
        self.assertEqual(storage.load_progress(), 0)

    def test_round_trip(self) -> None:
        storage.save_progress(4)
        self.assertEqual(storage.load_progress(), 4)
        self.assertTrue((self.data_dir / "progress.json").exists())

    def test_corrupted_file_means_level_one(self) -> None:
        (self.data_dir / "progress.json").write_text('{"unlocked": "beaucoup"}', encoding="utf-8")
        with self.assertLogs(storage.logger, "ERROR"):
            self.assertEqual(storage.load_progress(), 0)

    def test_scores_still_use_scores_json(self) -> None:
        storage.save_entries([{"name": "a", "points": 10, "levels": 1}])
        self.assertTrue((self.data_dir / "scores.json").exists())
        self.assertEqual(storage.load_entries()[0]["name"], "a")


if __name__ == "__main__":
    unittest.main()
