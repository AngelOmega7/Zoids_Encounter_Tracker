"""Sync the revised ability families from the sibling Character Sheet catalog."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / "Character_Sheet_app/zoids_app/data/abilities.json"
FAMILIES = {
    "iron_defense", "shield_master", "armor_breaker", "economized_shooting",
    "evasion_master", "anti_air_pro", "laser_expert", "missile_expert",
    "particle_expert", "melee_expert", "rifle_expert", "melee_multi_attack",
    "ranged_multi_attack", "sniper", "true_tank", "smoke_master", "fleet_footed",
    "small_expert", "counter_attack",
}
RANK_FOUR_FAMILIES = {"small_expert", "medium_expert", "medium_under_expert"}
RANK_TWO_FAMILIES = {"small_expert"}


def sync(source=SOURCE, destination=ROOT / "Zoid_Abilities.csv"):
    catalog = json.loads(Path(source).read_text(encoding="utf-8"))
    records = [a for a in catalog["records"] if a.get("family") in FAMILIES
               or (a.get("family") in RANK_FOUR_FAMILIES and a.get("rank") == 4)
               or (a.get("family") in RANK_TWO_FAMILIES and a.get("rank") == 2)]
    by_name = {name.strip().casefold(): a for a in records
               for name in (a["name"], *a.get("legacy_names", []))}
    with Path(destination).open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        columns, rows = reader.fieldnames, list(reader)
    seen = set()
    for row in rows:
        record = by_name.get(row[columns[0]].strip().casefold())
        if record is None:
            continue
        seen.add(record["id"])
        for header, key in zip(columns, catalog["columns"]):
            value = record["fields"].get(key)
            row[header] = "" if value is None else value
        row[columns[0]] = record["name"]
    missing = {a["id"] for a in records} - seen
    if missing:
        raise ValueError(f"Missing tracker ability rows: {sorted(missing)}")
    with Path(destination).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return len(seen)


if __name__ == "__main__":
    print(f"Synced {sync()} ability ranks from the Character Sheet app.")
