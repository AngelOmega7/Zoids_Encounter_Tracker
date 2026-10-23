import random
import pandas as pd
from data_paths import ZOIDS_CSV, validate_csv

df = pd.read_csv(validate_csv(ZOIDS_CSV))


def generate_encounter(encounter_level, exclude_blox=False):
    encounter_level_mod = encounter_level + 2

    # Secure numeric comparison filtering out non-numeric cells safely
    numeric_levels = pd.to_numeric(df["Level Required 5"], errors='coerce')
    filtered_df = df[numeric_levels <= int(encounter_level_mod)].copy()

    if exclude_blox and "Type 3" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["Type 3"].astype(str).str.upper() != "BLOX"]

    if filtered_df.empty:
        return []

    spawn_count = random.randint(3, 6)
    mob = []
    difficulty = 0

    for _ in range(spawn_count):
        random_row = filtered_df.sample(n=1)
        chosen_item = random_row['Name 1'].iloc[0]
        chosen_level = random_row['Level Required 5'].iloc[0]

        try:
            chosen_HP = int(random_row['Health 6'].iloc[0])
            chosen_armor = int(random_row['Armor 7'].iloc[0])
            chosen_defense = int(random_row['Defense 8'].iloc[0])
        except (ValueError, TypeError):
            continue

        if difficulty + chosen_level < encounter_level * 3:
            difficulty = difficulty + chosen_level
            mob.append({
                "Name": chosen_item, "LV": chosen_level,
                "HP": chosen_HP, "AR": chosen_armor, "DF": chosen_defense
            })

    return mob
