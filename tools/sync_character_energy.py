"""Refresh bundled Zoid/Energy data from the sibling Character Sheet app."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / "Character_Sheet_app/zoids_app/data"


def sync():
    existing = json.loads((ROOT / "zoids.json").read_text())
    levels = {record["id"]: record["fields"].get("required_level") for record in existing["records"]}
    zoids = json.loads((SOURCE / "zoids.json").read_text())
    transports = json.loads((SOURCE / "transports.json").read_text())
    zoids["records"].extend(transports["records"])
    # The tracker retains its own required levels, independently of the sheet app.
    zoids["columns"][4] = "required_level"
    zoids["source_headers"][4] = existing["source_headers"][4]
    for record in zoids["records"]:
        fields = list(record["fields"].items())
        record["fields"] = dict([*fields[:4], ("required_level", levels[record["id"]]), *fields[4:]])
        assert type(record["energy"]) is int and record["energy"] > 0
        assert type(record["energy_recharge"]) is int and record["energy_recharge"] >= 0
        assert len(record["energy_costs"]) == 8
    zoids["energy_data_version"] = json.loads((SOURCE / "manifest.json").read_text())["data_version"]
    (ROOT / "zoids.json").write_text(json.dumps(zoids, indent=2, ensure_ascii=False) + "\n")
    # Keep the CSV fallback and generator's gear fields aligned as well.
    restored = {alias.casefold(): record for record in zoids["records"] if record.get("removable_weapon_restore")
                for alias in (record["name"], *record.get("legacy_names", []))}
    path = ROOT / "ZoidsDB.csv"
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        columns, rows = reader.fieldnames, list(reader)
    for row in rows:
        record = restored.get(row["Name 1"].strip().casefold())
        if record:
            for key, header in zip(zoids["columns"][12:71], zoids["source_headers"][12:71]):
                if header in row:
                    value = record["fields"].get(key)
                    row[header] = "" if value is None else value
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    path = ROOT / "Zoid_Abilities.csv"
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        columns, rows = reader.fieldnames, list(reader)
    rows = [row for row in rows if not row[columns[0]].strip().startswith("Economized Shooting")]
    abilities = json.loads((SOURCE / "abilities.json").read_text())["records"]
    for ability in abilities:
        if ability.get("family") == "economized_shooting":
            row = dict.fromkeys(columns, "")
            row[columns[0]] = ability["name"]
            row[columns[1]] = ability["fields"]["description"]
            rows.append(row)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Synced {len(zoids['records'])} Zoid/transport records and four Economized Shooting ranks.")


if __name__ == "__main__":
    sync()
