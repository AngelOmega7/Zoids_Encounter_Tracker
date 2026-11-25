"""One-time migration of archived CSV inputs to standalone JSON catalogs."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def convert(source=ROOT / "source", destination=ROOT):
    def rows(name):
        with (source / name).open(encoding="utf-8-sig", newline="") as handle:
            return list(csv.reader(handle))

    def write(name, payload):
        (destination / name).write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    for old, new in (("Zoid_Abilities.csv", "abilities.json"), ("LootDB.csv", "loot.json")):
        table = rows(old)
        columns = [c.strip() for c in table[0]]
        write(new, {"schema_version": 1, "columns": columns,
                    "records": [dict(zip(columns, row)) for row in table[1:] if row and row[0].strip()]})
    styles = {}
    names = iter(("Tank", "Fighter", "Scout", "Almighty"))
    current = None
    for row in rows("Stats.csv"):
        if not row or not row[0].strip():
            continue
        if row[0].strip().casefold() == "level":
            current = []
            styles[next(names)] = current
        elif current is not None and len(row) >= 6:
            current.append(dict(zip(("level", "health", "armor", "react", "perception", "to_hit"), row)))
    write("stats.json", {"schema_version": 1, "styles": styles})

    table = rows("ZoidsDB.csv")
    old_zoids = [dict(zip((c.strip() for c in table[0]), row)) for row in table[1:] if row and row[0].strip()]
    # Preserve generator candidates and their original stats independently from
    # the corrected enemy-card catalog, matching the pre-migration behavior.
    keys = {"name": "Name 1", "type": "Type 3", "level": "Level Required 5",
            "health": "Health 6", "armor": "Armor 7", "defense": "Defense 8"}
    write("encounters.json", {"schema_version": 1,
          "records": [{key: row.get(column, "") for key, column in keys.items()} for row in old_zoids]})

    zoids = json.loads((destination / "zoids.json").read_text())
    aliases = {}
    normal = lambda name: " ".join(name.casefold().split())
    for record in zoids["records"]:
        record["tracker_names"] = []
        for name in (record["fields"]["name"], *record.get("legacy_names", [])):
            aliases.setdefault(normal(name), record)
    for old, new in (("Strum Fury (CAU)", "Sturm Fury (CAU)"), ("Zero Jeager (CAU)", "Zero Jager (CAU)")):
        if normal(new) in aliases:
            aliases[normal(old)] = aliases[normal(new)]
    for row in old_zoids:
        name = row["Name 1"].strip()
        if normal(name) not in aliases:
            raise ValueError(f"Missing corrected JSON record for {name}")
        aliases[normal(name)]["tracker_names"].append(name)
    for record in zoids["records"]:
        if not record["tracker_names"]:
            record["tracker_names"] = [record["fields"]["name"]]
    write("zoids.json", zoids)


if __name__ == "__main__":
    convert()
