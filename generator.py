"""Random encounter selection from the JSON encounter catalog."""
import json
import random
from data_paths import ENCOUNTERS_JSON, validate_catalog


def generate_encounter(encounter_level, exclude_blox=False):
    records = json.loads(validate_catalog(ENCOUNTERS_JSON).read_text(encoding="utf-8"))["records"]
    candidates = []
    for row in records:
        try:
            level = float(row["level"])
        except (ValueError, TypeError):
            continue
        if level <= int(encounter_level + 2) and not (exclude_blox and row["type"].upper() == "BLOX"):
            candidates.append(row)
    if not candidates:
        return []
    mob, difficulty = [], 0
    for _ in range(random.randint(3, 6)):
        row = random.choice(candidates)
        try:
            health, armor, defense = (int(row[key]) for key in ("health", "armor", "defense"))
            level = int(row["level"])
        except (ValueError, TypeError):
            continue
        if difficulty + level < encounter_level * 3:
            difficulty += level
            mob.append({"Name": row["name"], "LV": level, "HP": health, "AR": armor, "DF": defense})
    return mob
