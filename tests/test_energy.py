import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace

import energy
import enemy_stats
from enemy_sets import EnemySetStore

ROOT = Path(__file__).resolve().parents[1]


class EnergyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = enemy_stats.load_enemy_data(*(ROOT / name for name in
            ('ZoidsDB.csv', 'Stats.csv', 'Zoid_Abilities.csv', 'zoids.json')))

    def test_actions_and_invalid_inputs(self):
        self.assertEqual(energy.act('23', '25', 'start', '3'), 25)
        self.assertEqual(energy.act('2', '25', 'start', '3'), 5)
        for current in ('0', '25'):
            self.assertEqual(energy.act(current, '25', 'rest'), 12)
        self.assertEqual(energy.act('2', '25', 'use', '2'), 0)
        self.assertEqual(energy.act('0', '25', 'use', '0'), 0)
        for amount in ('', '-1', '1.5', True, None):
            with self.assertRaises(ValueError):
                energy.act('2', '25', 'use', amount)
        with self.assertRaises(ValueError):
            energy.act('2', '25', 'use', '3')
        with self.assertRaises(ValueError):
            energy.act('26', '25', 'start', '3')

    def test_start_turn_pays_upkeep_after_capped_recharge(self):
        self.assertEqual(energy.act('25', '25', 'start', '3', upkeep=2), 23)
        self.assertEqual(energy.act('0', '25', 'start', '3', upkeep=2), 1)
        with self.assertRaisesRegex(ValueError, 'Deactivate equipment'):
            energy.act('0', '25', 'start', '3', upkeep=4)
        with self.assertRaises(ValueError):
            energy.act('5', '25', 'start', '3', upkeep=-1)

    def test_catalog_and_economized_ranks(self):
        for zoid in self.data.zoids.values():
            base = enemy_stats.calculate_enemy_stats(zoid, 1, '', [], self.data)
            self.assertGreater(int(base.energy), 0, zoid.name)
            self.assertGreaterEqual(int(base.ept), 0)
            records = zoid.weapons + zoid.removable_equipment
            self.assertLessEqual(len(base.weapons), 8)
            for rank in range(1, 5):
                name = 'Economized Shooting' + (f' {rank}' if rank > 1 else '')
                result = enemy_stats.calculate_enemy_stats(zoid, 1, '', [name], self.data)
                for source, weapon in zip(records, result.weapons):
                    if source.name:
                        self.assertIsNotNone(source.energy_cost, (zoid.name, source.name))
                        expected = min(source.energy_cost, max(2, source.energy_cost - rank * 2)) if 'ranged' in source.tags else source.energy_cost
                        self.assertEqual(int(weapon.energy_cost), expected)

    def test_old_and_new_snapshots_preserve_edits(self):
        result = enemy_stats.calculate_enemy_stats(self.data.zoids['Shield Liger'], 1, '', [], self.data)
        saved = {'hp': '7', 'weapons': [[result.weapons[2].name, '+99', 'custom'],
                                     ['Custom cannon', '1', '2']], 'abilities': ['Economized Shooting']}
        migrated = energy.migrate(saved, result)
        self.assertEqual(migrated['hp'], '7')
        self.assertEqual(migrated['weapons'], saved['weapons'])
        self.assertEqual(migrated['weapon_costs'], ['2', ''])
        self.assertEqual((migrated['energy'], migrated['max_energy'], migrated['ept']), ('13', '26', '3'))
        migrated.update(energy='1', max_energy='41', ept='9')
        with tempfile.TemporaryDirectory() as directory:
            store = EnemySetStore(Path(directory) / 'test.db')
            key = store.save('test', [migrated])
            loaded = store.load(key)[1][0]
            self.assertEqual(energy.migrate(loaded, result), migrated)
        self.assertNotIn('energy', saved)

    def test_actual_level_excludes_type_bonus_and_migrates_old_energy_once(self):
        zoid = self.data.zoids['Shield Liger']
        plain = enemy_stats.calculate_enemy_stats(zoid, 10, '', [], self.data)
        ability = next(a.name for a in self.data.abilities.values() if a.type_bonus == zoid.type and a.level_bonus > 0)
        boosted = enemy_stats.calculate_enemy_stats(zoid, 10, '', [ability], self.data)
        self.assertGreater(boosted.effective_level, plain.effective_level)
        self.assertEqual((plain.energy, boosted.energy), ('35', '35'))
        self.assertEqual(plain.ept, boosted.ept)
        old = dict(energy='7', max_energy='45', ept='9', weapons=[])
        migrated = energy.migrate(old, boosted)
        self.assertEqual((migrated['energy'], migrated['max_energy'], migrated['ept']), ('7', '55', '9'))
        self.assertEqual(energy.migrate(migrated, boosted), migrated)


def walk(control):
    yield control
    for child in getattr(control, 'controls', []) or []:
        yield from walk(child)
    content = getattr(control, 'content', None)
    if content is not None and not isinstance(content, str):
        yield from walk(content)


class EnemyEnergyUITests(unittest.TestCase):
    def setUp(self):
        import main
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.page = SimpleNamespace(overlay=[], width=1000, controls=[], update=lambda: None)
        self.page.add = lambda c: self.page.controls.append(c)
        with patch.object(main, 'EnemySetStore', lambda: EnemySetStore(Path(self.temp.name) / 'test.db')):
            main.main(self.page)
        nav = self.page.navigation_bar
        nav.selected_index = 1
        nav.on_change(None)
        self.controls = list(walk(self.page.controls[0]))
        self.cards = [c.data for c in self.controls if getattr(c, 'label', '') == 'Select Zoid']

    def button(self, name, index=0):
        return [c for c in self.controls if getattr(c, 'content', None) == name][index]

    def select(self, card):
        card['zoid'].value = 'Shield Liger'
        card['zoid'].on_select(None)

    def test_independent_actions_and_recalculation(self):
        first, second = self.cards[:2]
        self.select(first)
        self.select(second)
        self.assertEqual(first['energy'].value, '16')
        self.button('Start Turn').on_click(None)
        self.assertEqual(first['energy'].value, '19')
        self.assertEqual(second['energy'].value, '16')
        first['energy'].value = '1'
        self.button('Use', 2).on_click(None)
        self.assertEqual(first['energy'].value, '1')
        first['energy'].value = '8'
        self.button('Use', 2).on_click(None)
        self.assertEqual(first['energy'].value, '6')
        first['ept'].value = '10'
        first['level'].on_change(None)
        self.assertEqual((first['energy'].value, first['ept'].value), ('6', '10'))
        self.button('Rest').on_click(None)
        self.assertEqual(first['energy'].value, '16')

    def test_active_shields_invisibility_and_organoid_upkeep(self):
        card = self.cards[0]
        self.select(card)
        index = next(i for i, hp in enumerate(card['shield_hp']) if int(hp.value) > 0)
        card['equipment_active'][index].value = True
        card['abilities'][0].value = 'Shield Master 4'
        card['abilities'][0].on_select(None)
        card['organoid_shields'].value = '100'
        card['shield_damage'].value = '30'
        card['refresh_shields'](None)
        self.assertEqual(card['shield_summary'].value, 'Shields 470 / 500 · Upkeep 2/turn')
        card['energy'].value = card['max_energy'].value
        maximum = int(card['max_energy'].value)
        self.button('Start Turn').on_click(None)
        self.assertEqual(int(card['energy'].value), maximum - 2)
        card['equipment_active'][index].value = False
        card['refresh_shields'](None)
        self.assertEqual(card['shield_summary'].value, 'Shields 320 / 350 · Upkeep 0/turn')
        self.button('Start Turn').on_click(None)
        self.assertEqual(int(card['energy'].value), maximum)
        card['zoid'].value = 'Shadow Fox'
        card['zoid'].on_select(None)
        invisible = next(i for i, flag in enumerate(card['invisibility']) if flag.value)
        self.assertEqual(invisible, 7)
        card['equipment_active'][invisible].value = True
        card['energy'].value = '10'
        card['ept'].value = '1'
        self.button('Start Turn').on_click(None)
        self.assertEqual(card['energy'].value, '8')
        card['energy'].value = '0'
        self.button('Start Turn').on_click(None)
        self.assertEqual(card['energy'].value, '0')
        self.assertTrue(card['equipment_active'][invisible].value)

    def test_shield_state_persists_and_old_sets_default_inactive(self):
        card = self.cards[0]
        self.select(card)
        index = next(i for i, hp in enumerate(card['shield_hp']) if int(hp.value) > 0)
        card['equipment_active'][index].value = True
        card['shield_hp'][index].value = '220'
        card['shield_damage'].value = '40'
        card['organoid_shields'].value = '60'
        card['invisibility'][index].value = True  # Same item pays upkeep only once.
        card['refresh_shields'](None)
        next(c for c in self.controls if getattr(c, 'label', '') == 'Enemy set name').value = 'Shields'
        self.button('Save New Set').on_click(None)
        self.button('Clear All Enemies').on_click(None)
        self.assertEqual(card['shield_summary'].value, 'Shields 0 / 0 · Upkeep 0/turn')
        self.button('Load Set').on_click(None)
        self.assertEqual(card['shield_summary'].value, 'Shields 240 / 280 · Upkeep 2/turn')
        self.assertTrue(card['equipment_active'][index].value)
        self.assertTrue(card['invisibility'][index].value)
        card['level'].on_change(None)
        self.assertEqual(card['shield_hp'][index].value, '220')
        self.assertEqual(card['shield_damage'].value, '40')

    def test_level_changes_preserve_manual_bonus_and_clamp_without_refill(self):
        card = self.cards[0]
        self.select(card)
        card['max_energy'].value = str(25 + int(card['level'].value) + 20)
        card['energy'].value = '7'
        card['level'].value = '10'
        card['level'].on_change(None)
        self.assertEqual((card['max_energy'].value, card['energy'].value, card['ept'].value), ('55', '7', '3'))
        card['energy'].value = '55'
        card['level'].value = '2'
        card['level'].on_change(None)
        self.assertEqual((card['max_energy'].value, card['energy'].value), ('47', '47'))

    def test_save_load_and_clear(self):
        card = self.cards[0]
        self.select(card)
        card['energy'].value = '4'
        card['ept'].value = '11'
        card['hp'].value = '7'
        card['weapon_costs'][2].value = '5'
        next(c for c in self.controls if getattr(c, 'label', '') == 'Enemy set name').value = 'Ambush'
        self.button('Save New Set').on_click(None)
        self.button('Clear All Enemies').on_click(None)
        self.assertEqual(card['energy'].value, '')
        self.button('Load Set').on_click(None)
        self.assertEqual((card['energy'].value, card['ept'].value, card['hp'].value), ('4', '11', '7'))
        self.assertEqual(card['weapon_costs'][2].value, '5')

    def test_temporary_stats_save_recalculate_and_rest_independently(self):
        first, second = self.cards[:2]
        self.select(first)
        self.select(second)
        armor, defense = int(first['armor'].value), int(first['defense'].value)
        def click(tooltip):
            next(c for c in self.controls if getattr(c, 'tooltip', None) == tooltip).on_click(None)
        click('Decrease armor by 1 (until Rest)')
        click('Decrease armor by 1 (until Rest)')
        click('Increase defense by 1 (until Rest)')
        first['level'].on_change(None)
        self.assertEqual((int(first['armor'].value), int(first['defense'].value)), (armor - 2, defense + 1))
        self.assertEqual(int(second['armor'].value), armor)
        next(c for c in self.controls if getattr(c, 'label', '') == 'Enemy set name').value = 'Modifiers'
        self.button('Save New Set').on_click(None)
        self.button('Clear All Enemies').on_click(None)
        self.button('Load Set').on_click(None)
        self.assertEqual(first['stat_modifiers'], {'armor': -2, 'defense': 1})
        first['defense'].value = str(defense + 11)  # Independent GM adjustment.
        self.button('Rest').on_click(None)
        self.assertEqual((int(first['armor'].value), int(first['defense'].value)), (armor, defense + 10))
        self.assertEqual(first['stat_modifiers'], {'armor': 0, 'defense': 0})

    def test_shadow_fox_slot_five_details_and_energy_spending(self):
        card = self.cards[0]
        card['zoid'].value = 'Shadow Fox'
        card['zoid'].on_select(None)
        self.assertEqual(card['weapons'][4][0].value, 'Laser Vulcan Gun')
        self.assertEqual(card['weapons'][4][2].value, '90')
        self.assertEqual(card['weapon_costs'][4].value, '8')
        self.assertIn('30m by 90m', card['weapons'][4][0].tooltip)
        self.assertIn('Close Range', card['weapons'][4][0].tooltip)
        self.assertTrue(card['weapon_rows'][7].visible)
        self.assertFalse(card['weapon_rows'][5].visible)
        self.assertFalse(card['weapon_rows'][6].visible)
        card['energy'].value = '20'
        self.button('Use', 4).on_click(None)
        self.assertEqual(card['energy'].value, '12')

    def test_legacy_load_preserves_manual_values_and_clears_extra_rows(self):
        saved = []
        for card in self.cards:
            self.select(card)
            values = {key: card[key].value for key in
                ('zoid', 'stats_type', 'level', 'hp', 'armor', 'defense', 'speed', 'range', 'reaction')}
            values.update(abilities=[''] * 6,
                          weapons=[[field.value for field in fields] for fields in card['weapons'][:5]],
                          unique_weapon_visible=False, effects='Saved effects')
            values['hp'] = '7'
            values['weapons'][2][2] = 'GM damage'
            saved.append(values)
            card['weapon_rows'][7].visible = True
            card['weapons'][7][0].value = 'Stale item'
        key = EnemySetStore(Path(self.temp.name) / 'test.db').save('Legacy', saved)
        next(c for c in self.controls if getattr(c, 'label', '') == 'Saved enemy sets').value = str(key)
        self.button('Load Set').on_click(None)
        for card in self.cards:
            self.assertEqual((card['hp'].value, card['energy'].value), ('7', '16'))
            self.assertFalse(any(field.value for field in card['equipment_active']))
            self.assertEqual(card['shield_damage'].value, '0')
            self.assertEqual(card['weapons'][2][2].value, 'GM damage')
            self.assertEqual(card['weapon_costs'][2].value, '2')
            self.assertFalse(card['weapon_rows'][7].visible)
            self.assertEqual(card['weapons'][7][0].value, '')
