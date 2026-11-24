import csv
import json
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
import unittest

import enemy_stats
from tools.sync_character_abilities import FAMILIES, SOURCE

ROOT = Path(__file__).resolve().parents[1]


class AbilitySyncTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = enemy_stats.load_enemy_data(*(ROOT / name for name in
            ('ZoidsDB.csv', 'Stats.csv', 'Zoid_Abilities.csv', 'zoids.json')))

    def test_revised_catalog_fields_match_character_sheet(self):
        if not SOURCE.exists():
            self.skipTest('Sibling Character Sheet catalog is unavailable')
        source = json.loads(SOURCE.read_text())
        with (ROOT / 'Zoid_Abilities.csv').open(newline='') as handle:
            reader = csv.DictReader(handle)
            headers = reader.fieldnames
            rows = {row[headers[0]]: row for row in reader}
        for record in source['records']:
            if record.get('family') not in FAMILIES:
                continue
            for header, key in zip(headers, source['columns']):
                value = record['name'] if key == 'name' else record['fields'].get(key)
                self.assertEqual(rows[record['name']][header], '' if value is None else str(value),
                                 (record['name'], key))

    def test_expert_matching_and_manual_anti_air(self):
        weapon = self.data.zoids['Shield Liger'].weapons[0]
        for family, tags in (('Laser Expert', {'laser'}), ('Missile Expert', {'explosive'}),
                             ('Particle Expert', {'particle'}), ('Melee Expert', {'melee'}),
                             ('Rifle Expert', {'ranged', 'bullet'})):
            for rank in range(1, 5):
                name = family if rank == 1 and family in ('Melee Expert', 'Rifle Expert') else f'{family} {rank}'
                ability = self.data.abilities[name]
                self.assertEqual(enemy_stats._weapon_expert_bonus(replace(weapon, tags=tags), [ability]), rank + 1)
        laser = self.data.abilities['Laser Expert 4']
        rifle = self.data.abilities['Rifle Expert 4']
        for tags, ability in (({'ranged', 'energy'}, laser), ({'ranged', 'piercing'}, rifle), ({'bullet'}, rifle)):
            self.assertEqual(enemy_stats._weapon_expert_bonus(replace(weapon, tags=tags), [ability]), 0)
        tagged = replace(weapon, tags={'melee', 'laser', 'anti-air'})
        abilities = [laser, self.data.abilities['Melee Expert 3'], self.data.abilities['Anti-Air Pro 4']]
        self.assertEqual(enemy_stats._weapon_expert_bonus(tagged, abilities), 5)
        self.assertEqual(enemy_stats._weapon_expert_bonus(tagged, abilities[-1:]), 0)

    def test_iron_defense_and_manual_rules_are_visible(self):
        zoid = self.data.zoids['Shield Liger']
        for rank in range(1, 5):
            name = 'Iron Defense' + (f' {rank}' if rank > 1 else '')
            result = enemy_stats.calculate_enemy_stats(zoid, 1, '', [name], self.data)
            self.assertEqual(int(result.defense), zoid.defense + 10 * rank)
        selected = ['Shield Master 4', 'True Tank 4', 'Sniper 4', 'Smoke Master 4', 'Evasion Master 4', 'Laser Expert 4']
        result = enemy_stats.calculate_enemy_stats(zoid, 1, '', selected, self.data)
        for name in selected:
            self.assertIn(self.data.abilities[name].description, result.summary)
        self.assertEqual(self.data.abilities['Shield Master 4'].shield, Decimal(250))
        old = enemy_stats.calculate_enemy_stats(zoid, 1, '', ['FLeet Footed 4'], self.data)
        self.assertEqual(int(old.speed), zoid.speed + 200)
        self.assertIn('Fleet Footed 4:', old.summary)
