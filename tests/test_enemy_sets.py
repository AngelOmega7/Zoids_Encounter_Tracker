import sqlite3
import tempfile
import unittest
from pathlib import Path

from enemy_sets import EnemySetStore


class EnemySetStoreTests(unittest.TestCase):
    def test_sets_survive_reopening_and_can_be_updated_and_deleted_independently(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data" / "enemies.sqlite3"
            store = EnemySetStore(path)
            cards = [{"zoid": "Shield Liger", "hp": "17", "abilities": ["", None],
                      "weapons": [["Custom weapon", "+3", "2d6"]]}]
            first = store.save("Ambush", cards)
            second = store.save("Boss", [])
            reopened = EnemySetStore(path)
            self.assertEqual(reopened.load(first), ("Ambush", cards))
            cards[0]["hp"] = "0"
            reopened.save("Ambush aftermath", cards, first)
            self.assertEqual(store.load(first), ("Ambush aftermath", cards))
            reopened.delete(second)
            self.assertEqual(store.list_sets(), [(first, "Ambush aftermath")])
            with self.assertRaises(ValueError):
                store.load(second)

    def test_invalid_names_and_conflicts_do_not_overwrite_saved_sets(self):
        with tempfile.TemporaryDirectory() as directory:
            store = EnemySetStore(Path(directory) / "enemies.sqlite3")
            first = store.save("Ambush", [{"hp": "25"}])
            second = store.save("Boss", [])
            with self.assertRaises(ValueError):
                store.save("  ", [])
            with self.assertRaises(sqlite3.IntegrityError):
                store.save(" ambush ", [])
            with self.assertRaises(sqlite3.IntegrityError):
                store.save("AMBUSH", [], second)
            self.assertEqual(store.load(first), ("Ambush", [{"hp": "25"}]))
            self.assertEqual(store.load(second), ("Boss", []))
            with self.assertRaises(ValueError):
                store.save("Missing", [], 999)


if __name__ == "__main__":
    unittest.main()
