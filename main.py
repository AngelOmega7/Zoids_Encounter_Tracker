import flet as ft
import sys
import generator  # Imports your core logic script safely
import loot
import enemy_stats
import sqlite3
from enemy_sets import EnemySetStore

def main(page: ft.Page):
    page.title = "Zoids TTRPG Tools"
    page.theme_mode = ft.ThemeMode.DARK
    # Responsive sizing is applied from page.on_resize below. Desktop keeps the
    # original dimensions; narrow screens use compact controls and stacked actions.
    is_mobile_layout = False
    control_width = 250
    if sys.platform == "win32":
        page.window.icon = "assets/icon.ico"
    # Common Subtitle used on both pages
    def create_subtitle():
        return ft.Text("Zoids TTRPG", size=16, italic=True, color=ft.Colors.BLUE_300)

    # --- SHARED ENCOUNTER UI DATA HOOKS ---
    encounter_results = ft.Column(spacing=10, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
    level_input = ft.TextField(
        label="Enter Encounter Level (1-50)",
        value="1",
        keyboard_type=ft.KeyboardType.NUMBER,
        width=250,
        text_align="center"
    )

    # --- SHARED ENCOUNTER UI DATA HOOKS ---
    exclude_blox_checkbox = ft.Checkbox(
        label="Exclude BLOX Zoids",
        value=False
    )

    # --- SHARED ENEMY/TRACKER DATA HOOKS ---
    enemy_data = None
    enemy_data_error = ""
    enemy_name_list = []
    ability_name_list = []
    stats_type_list = []
    try:
        from data_paths import (
            ZOIDS_CSV,
            ZOIDS_JSON,
            STATS_CSV,
            ABILITIES_CSV,
            validate_csv as _validate_csv,
        )
        enemy_data = enemy_stats.load_enemy_data(
            _validate_csv(ZOIDS_CSV),
            _validate_csv(STATS_CSV),
            _validate_csv(ABILITIES_CSV),
            zoids_json=ZOIDS_JSON,
        )
        enemy_name_list = list(enemy_data.zoid_names)
        ability_name_list = list(enemy_data.ability_names)
        stats_type_list = list(enemy_data.stats_type_names)
    except Exception as exc:
        enemy_data_error = str(exc)

    # --- SHARED LOOT UI DATA HOOKS ---
    loot_results = ft.Column(spacing=10, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

    loot_tier_dropdown = ft.Dropdown(
        label="Select Loot Tier",
        value="1",
        options=[
            ft.dropdown.Option("1"),
            ft.dropdown.Option("2"),
            ft.dropdown.Option("3"),
            ft.dropdown.Option("4"),
            ft.dropdown.Option("5"),
        ],
        width=250,
    )
    try:
      available_categories = ["All"] + loot.get_all_categories()
    except Exception:
      available_categories = ["All"]
    
    loot_category_dropdown = ft.Dropdown(
        label="Filter by Category",
        value="All",
        options=[ft.dropdown.Option(cat) for cat in available_categories],
        width=250,
    )

    loot_count_input = ft.TextField(
        label="Number of Items to Drop",
        value="1",
        keyboard_type=ft.KeyboardType.NUMBER,
        width=250,
        text_align="center"
    )

    blox_checkbox = ft.Checkbox(
        label="Include BLOX Items",
        value=False
    )

    # --- SHARED PARTY UI DATA HOOKS ---
    party_members = []
    party_results = ft.Column(spacing=10, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
    party_summary = ft.Text("No party members yet.", size=14, italic=True, color=ft.Colors.GREY_400)

    party_name_input = ft.TextField(
        label="Zoid Name",
        hint_text="e.g. Hellrunner",
        width=250,
    )

    party_level_input = ft.TextField(
        label="Level",
        value="1",
        keyboard_type=ft.KeyboardType.NUMBER,
        width=250,
        text_align="center"
    )

    party_hp_input = ft.TextField(
        label="Max HP",
        value="100",
        keyboard_type=ft.KeyboardType.NUMBER,
        width=250,
        text_align="center"
    )

    party_armor_input = ft.TextField(
        label="Armor",
        value="0",
        keyboard_type=ft.KeyboardType.NUMBER,
        width=250,
        text_align="center"
    )

    party_defense_input = ft.TextField(
        label="Defense",
        value="0",
        keyboard_type=ft.KeyboardType.NUMBER,
        width=250,
        text_align="center"
    )

    # --- CLICK HANDLERS ---
    def on_generate_click(e):
        encounter_results.controls.clear()
        try:
            lvl = int(level_input.value)
            if lvl < 1 or lvl > 50:
                raise ValueError
        except ValueError:
            encounter_results.controls.append(
                ft.Text("Please enter a valid integer between 1 and 50.", color=ft.Colors.RED_400)
            )
            page.update()  # Deep loop safe refresh
            return

        spawned_mob = generator.generate_encounter(lvl, exclude_blox=exclude_blox_checkbox.value)
        if not spawned_mob:
            encounter_results.controls.append(ft.Text("No Zoids found matching this level criteria."))
        else:
            encounter_results.controls.append(
                ft.Text(f"Generated {len(spawned_mob)} Enemies:", size=16, weight=ft.FontWeight.NORMAL)
            )
            for zoid in spawned_mob:
                hp_tracker = ft.TextField(
                    value=str(zoid['HP']),
                    width=70,
                    height=30,
                    text_size=14,
                    content_padding=5,
                    text_align="center",
                    keyboard_type=ft.KeyboardType.NUMBER,
                    border_color=ft.Colors.GREEN_700,
                    color=ft.Colors.GREEN_400
                )
                card = ft.Card(
                    content=ft.Container(
                        padding=12,
                        content=ft.Column([
                            ft.Text(zoid['Name'], size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_200),
                            ft.Row([
                                ft.Text(f"LV: {zoid['LV']}", weight=ft.FontWeight.NORMAL),
                                ft.Row([
                                    ft.Text("HP:", color=ft.Colors.GREEN_400, size=14),
                                    hp_tracker
                                ], spacing=5, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                                ft.Text(f"Armor: {zoid['AR']}", color=ft.Colors.ORANGE_400),
                                ft.Text(f"Def: {zoid['DF']}", color=ft.Colors.PURPLE_300),
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER, wrap=True)
                        ], spacing=5)
                    )
                )
                encounter_results.controls.append(card)
        page.update()  # Direct inline layout tree refresh

    def on_generate_loot_click(e):
        loot_results.controls.clear()
        try:
            count = int(loot_count_input.value)
            tier = int(loot_tier_dropdown.value)
            category = str(loot_category_dropdown.value)  # Capture Category layout state
            if count < 1:
                raise ValueError
        except ValueError:
            loot_results.controls.append(
                ft.Text("Please enter a valid number of items greater than 0.", color=ft.Colors.RED_400)
            )
            page.update()
            return

        # 🚀 Updated to pass category selection straight down into loot.py
        dropped_items = loot.generate_loot(
            num_items=count,
            target_tier=tier,
            target_category=category,
            include_blox=blox_checkbox.value
        )

        if dropped_items and isinstance(dropped_items, list) and len(dropped_items) == 1 and "Error" in str(
                dropped_items[0].get('Item', '')):
            loot_results.controls.append(ft.Text(dropped_items[0]['Item'], color=ft.Colors.RED_400))
        else:
            loot_results.controls.append(
                ft.Text(f"Generated {len(dropped_items)} {category if category != 'All' else ''} Tier {tier} Items:",
                        size=16, weight=ft.FontWeight.NORMAL)
            )

            for item in dropped_items:
                blox_val = item.get('BLOX')
                is_blox_item = str(blox_val) == "1" or blox_val == 1.0 or blox_val == 1

                type_label = f"{item.get('Category', 'General')}"
                if is_blox_item:
                    type_label += " [BLOX]"

                card = ft.Card(
                    content=ft.Container(
                        padding=12,
                        content=ft.Column([
                            ft.Text(
                                item.get('Item', 'Unknown Item'),
                                size=18,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.RED_200 if is_blox_item else ft.Colors.BLUE_200
                            ),
                            ft.Row([
                                ft.Text(f"Type: {type_label}", italic=True),
                                ft.Text(f"Tier {item.get('Tier', tier)}", color=ft.Colors.BLUE_300,
                                        weight=ft.FontWeight.BOLD),
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                        ], spacing=5)
                    )
                )
                loot_results.controls.append(card)
        page.update()

    def on_random_category_click(e):
        import random
        # 1. Isolate just the actual game categories (skip the "All" filter)
        game_categories = [cat for cat in loot.get_all_categories() if cat != "All"]

        if not game_categories:
            page.overlay.append(ft.SnackBar(ft.Text("No categories found in LootDB.csv.")))
            page.update()
            return

        # 2. Pick a random category choice
        random_choice = random.choice(game_categories)

        # 3. Update the dropdown interface value automatically
        loot_category_dropdown.value = random_choice

        # 4. Display a clean popup notification toast to the user
        page.overlay.append(
            ft.SnackBar(
                content=ft.Text(f"Selected Random Category: {random_choice}", weight=ft.FontWeight.BOLD),
                bgcolor=ft.Colors.BLUE_900,
                open=True
            )
        )
        page.update()

    # --- PARTY HANDLERS ---
    def show_message(message):
        page.overlay.append(
            ft.SnackBar(
                content=ft.Text(message, weight=ft.FontWeight.BOLD),
                bgcolor=ft.Colors.BLUE_900,
                open=True
            )
        )
        page.update()

    def commit_party_hp(e, member, field):
        try:
            new_hp = int(e.control.value)
        except (TypeError, ValueError):
            new_hp = member["HP"]
        member["HP"] = max(0, min(member["MaxHP"], new_hp))
        field.value = str(member["HP"])
        page.update()

    def adjust_party_hp(member, delta, field):
        member["HP"] = max(0, min(member["MaxHP"], member["HP"] + delta))
        field.value = str(member["HP"])
        page.update()

    def remove_party_member(member):
        if member in party_members:
            party_members.remove(member)
        render_party()

    def render_party():
        party_results.controls.clear()

        if not party_members:
            party_summary.value = "No party members yet."
            party_results.controls.append(
                ft.Text(
                    "Add a Zoid to start building your party.",
                    color=ft.Colors.GREY_400,
                    text_align=ft.TextAlign.CENTER,
                )
            )
            page.update()
            return

        member_count = len(party_members)
        party_summary.value = f"{member_count} Zoid{'s' if member_count != 1 else ''} in party"

        for member in party_members:
            hp_field = ft.TextField(
                value=str(member["HP"]),
                width=70,
                height=34,
                text_size=14,
                content_padding=5,
                text_align="center",
                keyboard_type=ft.KeyboardType.NUMBER,
                border_color=ft.Colors.GREEN_700,
                color=ft.Colors.GREEN_400,
            )
            hp_field.on_blur = lambda e, m=member, f=hp_field: commit_party_hp(e, m, f)
            hp_field.on_submit = lambda e, m=member, f=hp_field: commit_party_hp(e, m, f)

            card = ft.Card(
                content=ft.Container(
                    padding=12,
                    content=ft.Column([
                        ft.Row([
                            ft.Text(member["Name"], size=18, weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.BLUE_200),
                            ft.Row([
                                ft.Text(f"LV: {member['LV']}", weight=ft.FontWeight.NORMAL),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE_OUTLINE,
                                    icon_color=ft.Colors.RED_300,
                                    icon_size=18,
                                    tooltip="Remove from party",
                                    on_click=lambda e, m=member: remove_party_member(m),
                                ),
                            ], spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER, wrap=True),
                        ft.Row([
                            ft.Text("HP:", color=ft.Colors.GREEN_400, size=14),
                            hp_field,
                            ft.Text(f"/ {member['MaxHP']}", color=ft.Colors.GREEN_400, size=14),
                            ft.IconButton(
                                icon=ft.Icons.REMOVE,
                                icon_size=18,
                                tooltip="Damage 5",
                                on_click=lambda e, m=member, f=hp_field: adjust_party_hp(m, -5, f),
                            ),
                            ft.IconButton(
                                icon=ft.Icons.ADD,
                                icon_size=18,
                                tooltip="Heal 5",
                                on_click=lambda e, m=member, f=hp_field: adjust_party_hp(m, 5, f),
                            ),
                            ft.Text(f"Armor: {member['AR']}", color=ft.Colors.ORANGE_400),
                            ft.Text(f"Def: {member['DF']}", color=ft.Colors.PURPLE_300),
                        ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER, wrap=True),
                    ], spacing=5)
                )
            )
            party_results.controls.append(card)

        page.update()

    def on_add_party_member_click(e):
        name = (party_name_input.value or "").strip()
        try:
            lvl = int(party_level_input.value)
            max_hp = int(party_hp_input.value)
            armor = int(party_armor_input.value)
            defense = int(party_defense_input.value)
        except (TypeError, ValueError):
            show_message("Enter valid numbers for Level, Max HP, Armor, and Defense.")
            return

        if not name:
            show_message("Enter a name for the Zoid.")
            return

        if lvl < 1 or lvl > 50 or max_hp < 1 or armor < 0 or defense < 0:
            show_message("Level must be 1-50, Max HP at least 1, and Armor/Defense cannot be negative.")
            return

        party_members.append({
            "Name": name,
            "LV": lvl,
            "HP": max_hp,
            "MaxHP": max_hp,
            "AR": armor,
            "DF": defense,
        })

        party_name_input.value = ""
        party_level_input.value = "1"
        party_hp_input.value = "100"
        party_armor_input.value = "0"
        party_defense_input.value = "0"
        render_party()

    def on_clear_party_click(e):
        if not party_members:
            return
        party_members.clear()
        render_party()

    # --- BUTTON DECLARATIONS ---
    generate_btn = ft.Button(
        "Generate Encounter",
        on_click=on_generate_click,
        color=ft.Colors.WHITE,
        bgcolor=ft.Colors.BLUE_700
    )

    generate_loot_btn = ft.Button(
        "Roll Tier Loot",
        on_click=on_generate_loot_click,
        color=ft.Colors.WHITE,
        bgcolor=ft.Colors.BLUE_700
    )

    random_category_btn = ft.Button(
        "Random Category",
        on_click=on_random_category_click,
        color=ft.Colors.WHITE,
        bgcolor=ft.Colors.GREY_800
    )

    add_party_member_btn = ft.Button(
        "Add to Party",
        on_click=on_add_party_member_click,
        color=ft.Colors.WHITE,
        bgcolor=ft.Colors.BLUE_700
    )

    clear_party_btn = ft.Button(
        "Clear Party",
        on_click=on_clear_party_click,
        color=ft.Colors.WHITE,
        bgcolor=ft.Colors.GREY_800
    )

    # --- PERSISTENT VIEW LAYOUTS ---
    encounter_heading = ft.Text("Random Encounter Generator", size=28, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER)
    enemy_heading = ft.Text("Enemy", size=28, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER)
    party_heading = ft.Text("Party", size=28, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER)
    loot_heading = ft.Text("Random Loot Generator", size=28, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER)

    # The child layouts handle their own alignment. Avoid ft.alignment.center,
    # which is not available in some current Flet versions.
    category_controls = ft.Container(
        content=ft.Row(
            [loot_category_dropdown, random_category_btn],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
        ),
    )

    encounter_layout = ft.Column([
        encounter_heading,
        create_subtitle(),
        ft.Divider(height=20, color="transparent"),
        level_input,
        ft.Divider(height=10, color="transparent"),
        exclude_blox_checkbox,
        ft.Divider(height=10, color="transparent"),
        generate_btn,
        ft.Divider(height=20, color="transparent"),
        encounter_results
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, scroll=ft.ScrollMode.ADAPTIVE)

    # --- ENEMY/TRACKER UI BUILDERS ---
    enemy_cards_column = ft.Column(spacing=12, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
    enemy_card_data = []

    def event_value(control, event=None):
        if event is not None:
            candidate = getattr(event, "control", None)
            if candidate is not None and hasattr(candidate, "value"):
                return candidate.value
        return getattr(control, "value", None)

    def make_enemy_card(index):
        card_title = ft.Text(f"Enemy {index}", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_200)
        zoid_dropdown = ft.Dropdown(
            label="Select Zoid",
            options=[ft.dropdown.Option(n) for n in enemy_name_list],
            width=280,
            editable=True,
            enable_filter=True,
        )
        stats_type_dropdown = ft.Dropdown(
            label="Stats Type",
            value="",
            options=[ft.dropdown.Option(key="", text="None")]
            + [ft.dropdown.Option(name) for name in stats_type_list],
            width=190,
        )
        level_field = ft.TextField(
            label="Level (Stats)",
            width=150,
            keyboard_type=ft.KeyboardType.NUMBER,
            text_align="center",
        )

        hp_field = ft.TextField(label="HP / Health", width=150, keyboard_type=ft.KeyboardType.NUMBER, text_align="center")
        armor_field = ft.TextField(label="Armor", width=150, keyboard_type=ft.KeyboardType.NUMBER, text_align="center")
        defense_field = ft.TextField(label="Defense", width=150, keyboard_type=ft.KeyboardType.NUMBER, text_align="center")
        speed_field = ft.TextField(label="Speed", width=150, keyboard_type=ft.KeyboardType.NUMBER, text_align="center")
        range_field = ft.TextField(label="Range", width=150, keyboard_type=ft.KeyboardType.NUMBER, text_align="center")
        reaction_field = ft.TextField(label="Reaction", width=150, keyboard_type=ft.KeyboardType.NUMBER, text_align="center")

        ability_dropdowns = []
        for slot in range(1, 7):
            ability_dropdowns.append(
                ft.Dropdown(
                    label=f"Ability {slot}",
                    value="",
                    options=[ft.dropdown.Option(key="", text="None")]
                    + [ft.dropdown.Option(name) for name in ability_name_list],
                    width=245,
                    editable=True,
                    enable_filter=True,
                )
            )

        weapon_fields = []
        for w in range(1, 6):
            wname = ft.TextField(label=f"Weapon {w} Name", width=200)
            wtohit = ft.TextField(label=f"Weapon {w} To-Hit", width=140)
            wdamage = ft.TextField(label=f"Weapon {w} Damage", width=140)
            weapon_fields.append((wname, wtohit, wdamage))

        weapon_rows = []
        for wname_f, wtohit_f, wdamage_f in weapon_fields:
            weapon_rows.append(ft.Row([wname_f, wtohit_f, wdamage_f], wrap=True, alignment=ft.MainAxisAlignment.START))
        unique_weapon_row = weapon_rows[-1]
        unique_weapon_row.visible = False

        effects_text = ft.Text(
            "Select a Zoid to auto-populate stats.",
            size=11,
            italic=True,
            color=ft.Colors.GREY_400,
        )

        card_data = {
            "zoid": zoid_dropdown,
            "stats_type": stats_type_dropdown,
            "level": level_field,
            "abilities": ability_dropdowns,
            "hp": hp_field,
            "armor": armor_field,
            "defense": defense_field,
            "speed": speed_field,
            "range": range_field,
            "reaction": reaction_field,
            "weapons": weapon_fields,
            "weapon_rows": weapon_rows,
            "effects": effects_text,
        }
        zoid_dropdown.data = card_data
        enemy_card_data.append(card_data)

        def recalculate():
            zoid_name = zoid_dropdown.value
            zoid = enemy_data.zoids.get(zoid_name) if enemy_data else None
            if zoid is None:
                for key in ("hp", "armor", "defense", "speed", "range", "reaction"):
                    card_data[key].value = ""
                for wname_f, wtohit_f, wdamage_f in weapon_fields:
                    wname_f.value = ""
                    wtohit_f.value = ""
                    wdamage_f.value = ""
                unique_weapon_row.visible = False
                effects_text.value = "Select a Zoid to auto-populate stats."
                try:
                    page.update()
                except Exception:
                    pass
                return

            selected_abilities = [dropdown.value for dropdown in ability_dropdowns if dropdown.value]
            result = enemy_stats.calculate_enemy_stats(
                zoid,
                level_field.value,
                stats_type_dropdown.value,
                selected_abilities,
                enemy_data,
            )
            hp_field.value = result.health
            armor_field.value = result.armor
            defense_field.value = result.defense
            speed_field.value = result.speed
            range_field.value = result.range
            reaction_field.value = result.reaction
            for index, fields in enumerate(weapon_fields):
                wname_f, wtohit_f, wdamage_f = fields
                if index < len(result.weapons):
                    weapon = result.weapons[index]
                    wname_f.value = weapon.name
                    wtohit_f.value = weapon.to_hit
                    wdamage_f.value = weapon.damage
                else:
                    wname_f.value = ""
                    wtohit_f.value = ""
                    wdamage_f.value = ""
            unique_weapon_row.visible = len(result.weapons) > 4
            effects_text.value = result.summary
            try:
                page.update()
            except Exception:
                pass

        def on_zoid_selected(e=None):
            value = event_value(zoid_dropdown, e)
            if enemy_data is None or value not in enemy_data.zoids:
                return
            level_field.value = str(enemy_data.zoids[value].level_required)
            recalculate()

        def on_stats_type_change(e=None):
            value = event_value(stats_type_dropdown, e)
            if value and value not in stats_type_list:
                return
            recalculate()

        def make_ability_handler(dropdown):
            def on_ability_change(e=None):
                value = event_value(dropdown, e)
                if value and (enemy_data is None or value not in enemy_data.abilities):
                    return
                recalculate()
            return on_ability_change

        zoid_dropdown.on_select = on_zoid_selected
        stats_type_dropdown.on_select = on_stats_type_change
        for ability_dropdown in ability_dropdowns:
            ability_dropdown.on_select = make_ability_handler(ability_dropdown)
        level_field.on_change = lambda e: recalculate()

        stats_row = ft.Row([hp_field, armor_field, defense_field], wrap=True, alignment=ft.MainAxisAlignment.START)
        misc_row = ft.Row([speed_field, range_field, reaction_field], wrap=True, alignment=ft.MainAxisAlignment.START)

        content = ft.Container(
            padding=12,
            content=ft.Column([
                card_title,
                ft.Divider(height=5, color="transparent"),
                ft.Row([zoid_dropdown, stats_type_dropdown, level_field], wrap=True, spacing=10, run_spacing=8),
                ft.Divider(height=5, color="transparent"),
                ft.Text("Abilities (up to 6)", weight=ft.FontWeight.BOLD),
                ft.Row(ability_dropdowns[:3], wrap=True, spacing=10, run_spacing=8),
                ft.Row(ability_dropdowns[3:], wrap=True, spacing=10, run_spacing=8),
                effects_text,
                ft.Divider(height=5, color="transparent"),
                ft.Text("Stats", weight=ft.FontWeight.BOLD),
                stats_row,
                misc_row,
                ft.Divider(height=5, color="transparent"),
                ft.Text("Weapons", weight=ft.FontWeight.BOLD),
                *weapon_rows,
            ], spacing=6)
        )
        return ft.Card(content=content)

    for i in range(1, 7):
        enemy_cards_column.controls.append(make_enemy_card(i))

    def on_clear_enemies_click(e):
        for card in enemy_card_data:
            card["zoid"].value = None
            card["zoid"].text = ""
            card["stats_type"].value = ""
            for key in ("level", "hp", "armor", "defense", "speed", "range", "reaction"):
                card[key].value = ""
            for ability in card["abilities"]:
                ability.value = ""
                ability.text = ""
            for fields in card["weapons"]:
                for field in fields:
                    field.value = ""
            card["weapon_rows"][-1].visible = False
            card["effects"].value = "Select a Zoid to auto-populate stats."
        page.update()

    clear_enemies_btn = ft.Button(
        "Clear All Enemies",
        on_click=on_clear_enemies_click,
        color=ft.Colors.WHITE,
        bgcolor=ft.Colors.GREY_800,
    )

    # Store exact field values: loading must not recalculate away damage or edits.
    enemy_set_name = ft.TextField(label="Enemy set name", width=250)
    saved_enemy_sets = ft.Dropdown(label="Saved enemy sets", width=250)
    active_enemy_set_id = None
    enemy_set_status = ft.Text("Save your changes before loading another set.", size=12)
    enemy_store = None
    try:
        enemy_store = EnemySetStore()
        saved_enemy_sets.options = [
            ft.dropdown.Option(key=str(set_id), text=name)
            for set_id, name in enemy_store.list_sets()
        ]
    except (OSError, sqlite3.Error) as exc:
        enemy_store = None
        enemy_set_status.value = f"Enemy set storage unavailable: {exc}"

    enemy_value_keys = ("zoid", "stats_type", "level", "hp", "armor", "defense", "speed", "range", "reaction")

    def snapshot_enemies():
        return [
            {
                **{key: card[key].value for key in enemy_value_keys},
                "abilities": [field.value for field in card["abilities"]],
                "weapons": [[field.value for field in fields] for fields in card["weapons"]],
                "unique_weapon_visible": card["weapon_rows"][-1].visible,
                "effects": card["effects"].value,
            }
            for card in enemy_card_data
        ]

    def refresh_enemy_sets(selected=None):
        saved_enemy_sets.options = [
            ft.dropdown.Option(key=str(set_id), text=name)
            for set_id, name in enemy_store.list_sets()
        ]
        saved_enemy_sets.value = str(selected) if selected is not None else None

    def save_enemy_set(e, new=False):
        nonlocal active_enemy_set_id
        if not new and active_enemy_set_id is None:
            show_message("Load a set first, or use Save New Set.")
            return
        try:
            set_id = enemy_store.save(
                enemy_set_name.value or "", snapshot_enemies(),
                None if new else active_enemy_set_id,
            )
            active_enemy_set_id = set_id
            refresh_enemy_sets(set_id)
            enemy_set_status.value = f'Saved: {enemy_set_name.value.strip()}. Save again after editing.'
        except sqlite3.IntegrityError:
            show_message("An enemy set with that name already exists. Choose another name or load it to update it.")
            return
        except (OSError, sqlite3.Error, ValueError) as exc:
            show_message(f"Could not save enemy set: {exc}")
            return
        page.update()

    def load_enemy_set(e):
        nonlocal active_enemy_set_id
        if not saved_enemy_sets.value:
            show_message("Select a saved enemy set to load.")
            return
        try:
            name, cards = enemy_store.load(int(saved_enemy_sets.value))
            if len(cards) != len(enemy_card_data):
                raise ValueError("Unexpected number of enemy slots.")
            for card, saved in zip(enemy_card_data, cards):
                for key in enemy_value_keys:
                    card[key].value = saved[key]
                card["zoid"].text = saved["zoid"] or ""
                for field, value in zip(card["abilities"], saved["abilities"]):
                    field.value = value
                    field.text = value or ""
                for fields, values in zip(card["weapons"], saved["weapons"]):
                    for field, value in zip(fields, values):
                        field.value = value
                card["weapon_rows"][-1].visible = saved["unique_weapon_visible"]
                card["effects"].value = saved["effects"]
            active_enemy_set_id = int(saved_enemy_sets.value)
            enemy_set_name.value = name
            enemy_set_status.value = f"Loaded: {name}. Save changes before switching sets or closing the app."
        except (OSError, sqlite3.Error, ValueError, KeyError, TypeError) as exc:
            show_message(f"Could not load enemy set: {exc}")
            return
        page.update()

    def delete_enemy_set(e):
        nonlocal active_enemy_set_id
        if not saved_enemy_sets.value:
            show_message("Select a saved enemy set to delete.")
            return
        try:
            set_id = int(saved_enemy_sets.value)
            enemy_store.delete(set_id)
            if active_enemy_set_id == set_id:
                active_enemy_set_id = None
            refresh_enemy_sets()
            enemy_set_status.value = "Saved set deleted. Current enemies can be saved as a new set."
        except (OSError, sqlite3.Error, ValueError) as exc:
            show_message(f"Could not delete enemy set: {exc}")
            return
        page.update()

    enemy_set_controls = ft.Column([
        ft.Row([
            enemy_set_name,
            ft.Button("Save New Set", on_click=lambda e: save_enemy_set(e, new=True)),
            ft.Button("Save Changes", on_click=save_enemy_set),
        ], wrap=True, alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([
            saved_enemy_sets,
            ft.Button("Load Set", on_click=load_enemy_set),
            ft.Button("Delete Set", on_click=delete_enemy_set),
        ], wrap=True, alignment=ft.MainAxisAlignment.CENTER),
    ], disabled=enemy_store is None)

    enemy_layout = ft.Column([
        enemy_heading,
        create_subtitle(),
        ft.Divider(height=20, color="transparent"),
        ft.Row([clear_enemies_btn], alignment=ft.MainAxisAlignment.CENTER),
        enemy_set_controls,
        enemy_set_status,
        *(
            [ft.Text(f"Enemy data could not be loaded: {enemy_data_error}", color=ft.Colors.RED_400)]
            if enemy_data_error else []
        ),
        enemy_cards_column,
    ], horizontal_alignment=ft.CrossAxisAlignment.STRETCH, scroll=ft.ScrollMode.ADAPTIVE)

    party_actions = ft.Row(
        [add_party_member_btn, clear_party_btn],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=10,
        wrap=True,
    )

    party_layout = ft.Column([
        party_heading,
        create_subtitle(),
        ft.Divider(height=20, color="transparent"),
        party_name_input,
        party_level_input,
        party_hp_input,
        party_armor_input,
        party_defense_input,
        ft.Divider(height=10, color="transparent"),
        party_actions,
        ft.Divider(height=20, color="transparent"),
        party_summary,
        party_results
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, scroll=ft.ScrollMode.ADAPTIVE)

    loot_layout = ft.Column([
        loot_heading,
        create_subtitle(),
        ft.Divider(height=20, color="transparent"),
        loot_tier_dropdown,
        ft.Divider(height=10, color="transparent"),

        # The resize handler switches this between a row (desktop) and column (phone).
        category_controls,

        ft.Divider(height=10, color="transparent"),
        loot_count_input,
        ft.Divider(height=10, color="transparent"),
        blox_checkbox,
        ft.Divider(height=10, color="transparent"),
        generate_loot_btn,
        ft.Divider(height=20, color="transparent"),
        loot_results
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, scroll=ft.ScrollMode.ADAPTIVE)

    # --- FIXED MAIN CONTAINER ARCHITECTURE ---
    # We load a persistent parent container area instead of clear/adding nodes continuously
    main_view_container = ft.Container(content=encounter_layout, expand=True)

    def switch_tab(e):
        if nav_bar.selected_index == 0:
            main_view_container.content = encounter_layout
        elif nav_bar.selected_index == 1:
            main_view_container.content = enemy_layout
        elif nav_bar.selected_index == 2:
            main_view_container.content = party_layout
        elif nav_bar.selected_index == 3:
            main_view_container.content = loot_layout
        page.update()  # Safe view-swap content toggle trigger

    nav_bar = ft.NavigationBar(
        selected_index=0,
        on_change=switch_tab,
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.SHIELD, label="Encounters"),
            ft.NavigationBarDestination(icon=ft.Icons.PETS, label="Enemy"),
            ft.NavigationBarDestination(icon=ft.Icons.GROUPS, label="Party"),
            ft.NavigationBarDestination(icon=ft.Icons.CASINO, label="Loot"),
        ]
    )

    page.navigation_bar = nav_bar
    page.add(main_view_container)  # Single core structural load instance

    def apply_responsive_layout(e=None):
        """Compact the UI on narrow screens without changing desktop sizing."""
        nonlocal is_mobile_layout, control_width
        screen_width = page.width or 800
        mobile = screen_width < 600
        is_mobile_layout = mobile
        control_width = max(180, min(250, int(screen_width - 40))) if mobile else 250

        # Keep page headings clear of the Android status bar on phones.
        # Desktop layout remains unchanged.
        main_view_container.padding = ft.Padding(0, 24 if mobile else 0, 0, 0)

        # Inputs remain at their original 250px width on desktop.
        level_input.width = control_width
        loot_tier_dropdown.width = control_width
        loot_category_dropdown.width = control_width
        loot_count_input.width = control_width
        party_name_input.width = control_width
        party_level_input.width = control_width
        party_hp_input.width = control_width
        party_armor_input.width = control_width
        party_defense_input.width = control_width

        # Headings and spacing become more compact only on phones.
        heading_size = 21 if mobile else 28
        encounter_heading.size = heading_size
        enemy_heading.size = heading_size
        party_heading.size = heading_size
        loot_heading.size = heading_size
        encounter_layout.spacing = 6 if mobile else 10
        enemy_layout.spacing = 6 if mobile else 10
        party_layout.spacing = 6 if mobile else 10
        loot_layout.spacing = 6 if mobile else 10
        party_actions.width = control_width if mobile else None

        if mobile:
            category_controls.width = control_width
            category_controls.content = ft.Column(
                [loot_category_dropdown, ft.Container(content=random_category_btn, width=control_width)],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=4,
            )
        else:
            category_controls.width = None
            category_controls.content = ft.Row(
                [loot_category_dropdown, random_category_btn],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=10,
            )

        page.update()

    page.on_resize = apply_responsive_layout
    # Apply once after the initial layout; on_resize handles later rotation/resizing.
    apply_responsive_layout()


# --- UNIVERSAL PLATFORM DISPATCHER ---
if __name__ == "__main__":
    # Check if the active Flet version supports the new 'run' attribute
    if hasattr(ft, "run"):
        ft.run(main)  # Executes on your Flet 1.0+ Windows/Linux builds
    else:
        ft.app(target=main)  # Fallback for mobile environments running older Flet runtimes
