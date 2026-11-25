"""Refresh bundled Zoid/Energy JSON from the sibling Character Sheet app."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / "Character_Sheet_app/zoids_app/data"


def sync():
    existing = json.loads((ROOT / "zoids.json").read_text())
    previous = {record["id"]: record for record in existing["records"]}
    zoids = json.loads((SOURCE / "zoids.json").read_text())
    transports = json.loads((SOURCE / "transports.json").read_text())
    zoids["records"].extend(transports["records"])
    # Required levels and saved tracker names belong to the tracker, not the
    # Character Sheet. Preserve both across catalog refreshes.
    zoids["columns"][4] = "required_level"
    zoids["source_headers"][4] = existing["source_headers"][4]
    for record in zoids["records"]:
        old = previous.get(record["id"], {})
        fields = list(record["fields"].items())
        required_level = old.get("fields", {}).get("required_level", 1)
        record["fields"] = dict([*fields[:4], ("required_level", required_level), *fields[4:]])
        record["tracker_names"] = old.get("tracker_names", [record["fields"]["name"]])
        assert type(record["energy"]) is int and record["energy"] > 0
        assert type(record["energy_recharge"]) is int and record["energy_recharge"] >= 0
        assert len(record["energy_costs"]) == 8
    zoids["energy_data_version"] = json.loads((SOURCE / "manifest.json").read_text())["data_version"]
    (ROOT / "zoids.json").write_text(json.dumps(zoids, indent=2, ensure_ascii=False) + "\n")
    print(f"Synced {len(zoids['records'])} Zoid/transport records; tracker names and required levels retained.")


if __name__ == "__main__":
    sync()
