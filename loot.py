"""Weighted loot selection from the standalone JSON catalog."""
import json
import random
from data_paths import LOOT_JSON, validate_catalog


def _records():
    return json.loads(validate_catalog(LOOT_JSON).read_text(encoding="utf-8"))["records"]


def get_all_categories():
    try:
        return sorted({row["Category"] for row in _records() if row.get("Category")})
    except (OSError, ValueError) as exc:
        print(f"Could not load loot categories: {exc}")
        return []


def generate_loot(num_items: int, target_tier: int, target_category: str = "All", include_blox: bool = False):
    try:
        items = [row for row in _records()
                 if str(row["Tier"]) == str(target_tier)
                 and (target_category == "All" or row.get("Category") == target_category)
                 and (include_blox or int(row.get("BLOX") or 0) != 1)]
        if not items:
            return [{"Item": f"No items found matching Tier {target_tier} ({target_category}) constraints.", "Category": "System"}]
        weights = []
        for row in items:
            try:
                weights.append(float(row.get("Weight") or 0))
            except (ValueError, TypeError):
                weights.append(0)
        return random.choices(items, weights=weights, k=num_items)
    except Exception as exc:
        return [{"Item": f"Error rolling loot: {exc}", "Category": "System"}]
