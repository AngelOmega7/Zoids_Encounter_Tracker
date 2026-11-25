import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import generator
import loot

ROOT = Path(__file__).resolve().parents[1]


class JsonCatalogTests(unittest.TestCase):
    def test_runtime_loads_without_source_csvs_or_pandas(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            for name in ("enemy_stats.py", "generator.py", "loot.py", "data_paths.py",
                         "zoids.json", "stats.json", "abilities.json", "encounters.json", "loot.json"):
                shutil.copy2(ROOT / name, target / name)
            result = subprocess.run([sys.executable, "-S", "-B", "-c", """
import enemy_stats, generator, loot
data = enemy_stats.load_enemy_data('zoids.json', 'stats.json', 'abilities.json')
assert len(data.zoids) == 159
assert len(data.abilities) == 184
assert all(len(rows) == 100 for rows in data.stats.values())
assert data.zoids['Strum Fury (CAU)'].name == 'Strum Fury (CAU)'
assert isinstance(generator.generate_encounter(10), list)
assert loot.get_all_categories()
assert len(loot.generate_loot(3, 1)) == 3
"""], cwd=target, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_encounter_level_blox_and_budget_filters(self):
        rows = [dict(name="BLOX", type="BLOX", level="1", health="50", armor="10", defense="5"),
                dict(name="High", type="Wolf", level="50", health="50", armor="10", defense="5"),
                dict(name="Eligible", type="Wolf", level="2", health="80", armor="12", defense="8")]
        with tempfile.TemporaryDirectory() as directory:
            catalog = Path(directory) / "encounters.json"
            catalog.write_text(json.dumps({"records": rows}))
            with patch.object(generator, "ENCOUNTERS_JSON", catalog), patch.object(generator.random, "randint", return_value=6):
                result = generator.generate_encounter(2, exclude_blox=True)
        self.assertEqual([row["Name"] for row in result], ["Eligible", "Eligible"])
        self.assertEqual(result[0], dict(Name="Eligible", LV=2, HP=80, AR=12, DF=8))
        self.assertLess(sum(row["LV"] for row in result), 2 * 3)

    def test_loot_filtering_and_weights(self):
        rows = [dict(Item="Allowed", Category="Weapon", Tier="1", Weight="20", BLOX=""),
                dict(Item="BLOX", Category="Weapon", Tier="1", Weight="5", BLOX="1"),
                dict(Item="Other tier", Category="Weapon", Tier="2", Weight="100", BLOX=""),
                dict(Item="Other category", Category="Parts", Tier="1", Weight="100", BLOX="")]
        with patch.object(loot, "_records", return_value=rows), patch.object(loot.random, "choices", return_value=[rows[0]]) as choose:
            self.assertEqual(loot.generate_loot(1, 1, "Weapon"), [rows[0]])
            choose.assert_called_once_with([rows[0]], weights=[20.0], k=1)
            loot.generate_loot(2, 1, "Weapon", include_blox=True)
            choose.assert_called_with(rows[:2], weights=[20.0, 5.0], k=2)
            self.assertEqual(loot.generate_loot(1, 9)[0]["Category"], "System")
