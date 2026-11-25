import json
from pathlib import Path
import unittest

import enemy_stats

ROOT = Path(__file__).resolve().parents[1]


class GearSyncTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = enemy_stats.load_enemy_data(*(ROOT / name for name in
            ('zoids.json', 'stats.json', 'abilities.json')))

    def test_restored_weapons_use_slot_five_with_current_damage_and_energy(self):
        cases = (('Lightning Saix', 'Pulse Laser Gun:', 1, '110', '6'),
                 ('Lightning Saix BS', 'Pulse Laser Gun:', 1, '130', '8'),
                 ('Command Wolf IS', 'Long Range Rifle', 2, '130', '6'),
                 ('Shadow Fox', 'Laser Vulcan Gun', 2, '90', '8'))
        for name, weapon, old_index, damage, cost in cases:
            with self.subTest(zoid=name):
                stats = enemy_stats.calculate_enemy_stats(self.data.zoids[name], 1, '', [], self.data)
                self.assertEqual(stats.weapons[old_index].name, '')
                self.assertEqual((stats.weapons[4].name, stats.weapons[4].damage, stats.weapons[4].energy_cost),
                                 (weapon, damage, cost))

    def test_shadow_fox_aoe_tags_and_camouflage_slot(self):
        zoid = self.data.zoids['Shadow Fox']
        self.assertEqual(zoid.removable_equipment[0].tags, {'ranged', 'laser', 'close range'})
        stats = enemy_stats.calculate_enemy_stats(zoid, 1, '', [], self.data)
        self.assertIn('AoE attack targeting a 30m by 90m area', stats.weapons[4].details)
        self.assertIn('Optical Camouflage', stats.weapons[7].name)
        self.assertEqual(stats.weapons[7].energy_cost, '3')
        self.assertEqual([w.name for w in stats.weapons[5:7]], ['', ''])
        economized = enemy_stats.calculate_enemy_stats(zoid, 1, '', ['Economized Shooting'], self.data)
        self.assertEqual(economized.weapons[4].energy_cost, '6')

    def test_tracker_required_levels_remain_consistent_with_encounters(self):
        rows = {row['name']: row for row in json.loads((ROOT / 'encounters.json').read_text())['records']}
        for name in ('Lightning Saix', 'Lightning Saix BS', 'Command Wolf IS', 'Shadow Fox'):
            self.assertEqual(self.data.zoids[name].level_required, int(rows[name]['level']))

    def test_bundled_gear_matches_character_sheet_catalog(self):
        source = ROOT.parent / 'Character_Sheet_app/zoids_app/data/zoids.json'
        if not source.exists():
            self.skipTest('Sibling Character Sheet catalog is unavailable')
        current = {r['id']: r for r in json.loads(source.read_text())['records']}
        bundled = json.loads((ROOT / 'zoids.json').read_text())
        for record in bundled['records']:
            if record['id'] not in current:
                continue
            expected = current[record['id']]
            for column in bundled['columns'][12:71]:
                self.assertEqual(record['fields'][column], expected['fields'][column], (record['name'], column))
            self.assertEqual(record['energy_costs'], expected['energy_costs'], record['name'])
