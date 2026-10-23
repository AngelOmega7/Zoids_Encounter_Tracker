import os
import sys
import random
import pandas as pd
from data_paths import LOOT_CSV, validate_csv

df = pd.read_csv(validate_csv(LOOT_CSV))

def get_all_categories():
    try:
        df = pd.read_csv(validate_csv(LOOT_CSV))
        if "Category" in df.columns:
            categories = df["Category"].dropna().unique()
            return sorted(str(c) for c in categories)
        return []
    except (OSError, ValueError, pd.errors.ParserError) as exc:
        print(f"Could not load loot categories: {exc}")
        return []

def generate_loot(
    num_items: int,
    target_tier: int,
    target_category: str = "All",
    include_blox: bool = False,
):
  try:
    df = pd.read_csv(validate_csv(LOOT_CSV))

    # 1. Filter down strictly to the selected Tier
    tier_df = df[df["Tier"] == target_tier]

    # 2. NEW: Filter down by Category if a specific one is picked
    if target_category != "All" and "Category" in tier_df.columns:
      tier_df = tier_df[tier_df["Category"].astype(str) == target_category]

    # 3. Filter out BLOX items if the box is left unticked
    if "BLOX" in tier_df.columns and not include_blox:
      tier_df = tier_df[tier_df["BLOX"].fillna(0).astype(int) != 1]

    if tier_df.empty:
      return [
          {
              "Item": f"No items found matching Tier {target_tier} ({target_category}) constraints.",
              "Category": "System",
          }
      ]

    # 4. Extract weights and perform choice mapping
    weights = (
        pd.to_numeric(tier_df["Weight"], errors="coerce").fillna(0).tolist()
    )
    items = tier_df.to_dict(orient="records")

    # 5. Roll random items matching probabilities
    selected_loot = random.choices(items, weights=weights, k=num_items)
    return selected_loot

  except Exception as e:
    return [{"Item": f"Error rolling loot: {str(e)}", "Category": "System"}]
