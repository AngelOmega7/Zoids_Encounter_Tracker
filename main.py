import flet as ft
import sys
import generator  # Imports your core logic script safely
import loot

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
    try:
        import pandas as _pd
        from data_paths import ZOIDS_CSV, validate_csv as _validate_csv
        _enemy_df = _pd.read_csv(_validate_csv(ZOIDS_CSV))
        enemy_name_list = sorted([str(n) for n in _enemy_df['Name 1'].dropna().tolist() if str(n).strip()])
    except Exception:
        enemy_name_list = []

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

    def get_enemy_row_by_name(name):
        if not name or not enemy_name_list:
            return None
        try:
            import pandas as _pd
            from data_paths import ZOIDS_CSV, validate_csv as _validate_csv
            _df = _pd.read_csv(_validate_csv(ZOIDS_CSV))
            _rows = _df[_df['Name 1'].astype(str) == str(name)]
            if _rows.empty:
                return None
            return _rows.iloc[0]
        except Exception:
            return None

    def make_enemy_card(index):
        card_title = ft.Text(f"Enemy {index}", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_200)
        zoid_dropdown = ft.Dropdown(
            label="Select Zoid",
            options=[ft.dropdown.Option(n) for n in enemy_name_list],
            width=280,
            enable_filter=True,
        )
        hp_field = ft.TextField(label="HP / Health", width=150, keyboard_type=ft.KeyboardType.NUMBER, text_align="center")
        armor_field = ft.TextField(label="Armor", width=150, keyboard_type=ft.KeyboardType.NUMBER, text_align="center")
        defense_field = ft.TextField(label="Defense", width=150, keyboard_type=ft.KeyboardType.NUMBER, text_align="center")
        speed_field = ft.TextField(label="Speed", width=150, keyboard_type=ft.KeyboardType.NUMBER, text_align="center")
        range_field = ft.TextField(label="Range", width=150, keyboard_type=ft.KeyboardType.NUMBER, text_align="center")
        reaction_field = ft.TextField(label="Reaction", width=150, keyboard_type=ft.KeyboardType.NUMBER, text_align="center")

        weapon_fields = []
        for w in range(1, 5):
            wname = ft.TextField(label=f"Weapon {w} Name", width=200)
            wtohit = ft.TextField(label=f"Weapon {w} To-Hit", width=140)
            wdamage = ft.TextField(label=f"Weapon {w} Damage", width=140)
            weapon_fields.append((wname, wtohit, wdamage))

        zoid_dropdown.data = {
            "hp": hp_field,
            "armor": armor_field,
            "defense": defense_field,
            "speed": speed_field,
            "range": range_field,
            "reaction": reaction_field,
            "weapons": weapon_fields,
        }

        def populate_from_value(val):
            data = zoid_dropdown.data
            row = get_enemy_row_by_name(val)
            if row is None:
                return
            try:
                data["hp"].value = str(row['Health 6'])
            except Exception:
                data["hp"].value = ''
            try:
                data["armor"].value = str(row['Armor 7'])
            except Exception:
                data["armor"].value = ''
            try:
                data["defense"].value = str(row['Defense 8'])
            except Exception:
                data["defense"].value = ''
            try:
                data["speed"].value = str(row['Speed 9'])
            except Exception:
                data["speed"].value = ''
            try:
                data["range"].value = str(row['Range 11'])
            except Exception:
                data["range"].value = ''
            try:
                data["reaction"].value = str(row['Reaction 10'])
            except Exception:
                data["reaction"].value = ''
            try:
                wf = data["weapons"]
                wf[0][0].value = str(row['Weapon 1 13'])
                wf[0][1].value = str(row['To Hit 1  17'])
                wf[0][2].value = str(row['Damage 1 15'])
                wf[1][0].value = str(row['Weapon 2 19'])
                wf[1][1].value = str(row['To Hit 2  23'])
                wf[1][2].value = str(row['Damage 2  21'])
                wf[2][0].value = str(row['Weapon 3 30'])
                wf[2][1].value = str(row['To Hit 3 34'])
                wf[2][2].value = str(row['Damage 3 32'])
                wf[3][0].value = str(row['Weapon 4 41'])
                wf[3][1].value = str(row['To Hit 4 45'])
                wf[3][2].value = str(row['Damage 4 43'])
            except Exception:
                pass
            try:
                page.update()
            except Exception:
                pass

        def on_zoid_selected(e=None):
            val = getattr(zoid_dropdown, 'value', None)
            if val is None and e is not None and hasattr(e, 'control'):
                val = getattr(e.control, 'value', None)
            populate_from_value(val)

        def on_dropdown_change(e=None):
            val = getattr(e, 'control', zoid_dropdown).value if e is not None else zoid_dropdown.value
            populate_from_value(val)

        zoid_dropdown.on_select = on_zoid_selected
        zoid_dropdown.on_text_change = on_dropdown_change
        try:
            zoid_dropdown.on_change = on_zoid_selected
        except Exception:
            pass

        stats_row = ft.Row([hp_field, armor_field, defense_field], wrap=True, alignment=ft.MainAxisAlignment.START)
        misc_row = ft.Row([speed_field, range_field, reaction_field], wrap=True, alignment=ft.MainAxisAlignment.START)

        weapon_rows = []
        for wname_f, wtohit_f, wdamage_f in weapon_fields:
            weapon_rows.append(ft.Row([wname_f, wtohit_f, wdamage_f], wrap=True, alignment=ft.MainAxisAlignment.START))

        content = ft.Container(
            padding=12,
            content=ft.Column([
                card_title,
                ft.Divider(height=5, color="transparent"),
                zoid_dropdown,
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

    enemy_layout = ft.Column([
        enemy_heading,
        create_subtitle(),
        ft.Divider(height=20, color="transparent"),
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
