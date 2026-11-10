"""Validated, atomic per-enemy Energy actions and legacy snapshot defaults."""
import re
from copy import deepcopy


def whole(value, label):
    if isinstance(value, bool) or not re.fullmatch(r"[0-9]+", str(value).strip()):
        raise ValueError(f"{label} must be a nonnegative whole number.")
    return int(value)


def act(current, maximum, action, amount=None):
    maximum = whole(maximum, "Maximum Energy")
    if action == "rest":
        return maximum // 2
    current = whole(current, "Current Energy")
    if current > maximum:
        raise ValueError("Current Energy cannot exceed maximum Energy.")
    amount = whole(amount, "EPT" if action == "start" else "Energy Cost")
    if action == "start":
        return min(maximum, current + amount)
    if action == "use":
        if current < amount:
            raise ValueError(f"Not enough Energy: need {amount}, have {current}.")
        return current - amount
    raise ValueError("Unknown Energy action.")


def migrate(saved, result=None):
    """Add missing Energy fields without changing saved combat/manual edits."""
    saved = deepcopy(saved)
    maximum = result.energy if result else ""
    bonus = result.energy_level_bonus if result else 0
    if "max_energy" in saved and result and maximum:
        delta = bonus - saved.get("energy_level_bonus", 0)
        if delta:
            saved["max_energy"] = str(max(0, whole(saved["max_energy"], "Maximum Energy") + delta))
    saved["energy_level_bonus"] = bonus
    saved.setdefault("max_energy", maximum)
    saved.setdefault("energy", str(int(maximum) // 2) if maximum else "")
    saved.setdefault("ept", result.ept if result else "")
    costs = {w.name.casefold(): w.energy_cost for w in result.weapons} if result else {}
    saved.setdefault("weapon_costs", [costs.get(str(w[0]).casefold(), "") for w in saved["weapons"]])
    saved.setdefault("weapon_visibility", [True] * 4 + [saved.get("unique_weapon_visible", False)])
    return saved
