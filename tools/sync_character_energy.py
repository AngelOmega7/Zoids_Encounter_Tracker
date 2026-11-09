"""Refresh bundled Zoid/Energy data from the sibling Character Sheet app."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / "Character_Sheet_app/zoids_app/data"


def sync():
    zoids = json.loads((SOURCE / "zoids.json").read_text())
    transports = json.loads((SOURCE / "transports.json").read_text())
    zoids["records"].extend(transports["records"])
    for record in zoids["records"]:
        assert type(record["energy"]) is int and record["energy"] > 0
        assert type(record["energy_recharge"]) is int and record["energy_recharge"] >= 0
        assert len(record["energy_costs"]) == 8
    zoids["energy_data_version"] = json.loads((SOURCE / "manifest.json").read_text())["data_version"]
    (ROOT / "zoids.json").write_text(json.dumps(zoids, indent=2, ensure_ascii=False) + "\n")
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
