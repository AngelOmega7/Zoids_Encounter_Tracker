"""Enemy stat calculations for the encounter tracker.

The Enemy page uses the same data ideas as the Character Sheet app:

* ``ZoidsDB.csv`` supplies the Zoid's base stats and fixed weapons.
* ``zoids.json`` is the corrected Character Sheet catalog.  Matching records
  override the CSV values, including weapon layout and tag corrections.
* A removable weapon marked as usable only by its Zoid is appended as that
  Zoid's optional extra weapon.
* ``Stats.csv`` supplies the Tank / Fighter / Scout / Almighty level tables.
* ``Zoid_Abilities.csv`` supplies level, size, flat-stat, and Expert bonuses.

Only the standard library is used here so the calculation layer can be tested
without Flet or pandas.
"""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Iterable, Mapping, Sequence

STATS_TYPE_NAMES = ("Tank", "Fighter", "Scout", "Almighty")

# ZoidsDB stores one older spelling of this size.
SIZE_ALIASES = {
    "extra lare": "extra large",
}

# A few names differ between the CSV and the Character Sheet catalog beyond the
# aliases stored in zoids.json itself.
CSV_TO_JSON_NAME_OVERRIDES = {
    "strum fury (cau)": "sturm fury (cau)",
    "zero jeager (cau)": "zero jager (cau)",
}

JSON_WEAPON_COLUMNS = (
    ("weapon_1_13", "effect_2_14", "damage_1_15", "type_1_16", "to_hit_1_17"),
    ("weapon_2_19", "effect_3_20", "damage_2_21", "type_2_22", "to_hit_2_23"),
    ("weapon_3_30", "effect_4_31", "damage_3_32", "type_3_33", "to_hit_3_34"),
    ("weapon_4_41", "effect_5_42", "damage_4_43", "type_4_44", "to_hit_4_45"),
)

# Removable equipment can contain both generic gear and a weapon that is only
# usable by the Zoid it is attached to.  The source marks those unique weapons
# with "(... Only)" in the name or effect.
JSON_REMOVABLE_WEAPON_COLUMNS = (
    ("removable_equipment_47", "effect_6_48", "damage_5_49", "damage_type_50", "to_hit_5_51"),
    ("removable_equipment_2_54", "effect_7_56", "damage_6_55", "type_5_58", "to_hit_6_57"),
    ("removable_equipment_3_61", None, "damage_7_62", None, "to_hit_7_63"),
    ("removable_equipment_4_66", "effect_69", "damage_8_67", None, "to_hit_8_68"),
)

CSV_REMOVABLE_WEAPON_COLUMNS = (
    ("Removable Equipment 47", "Effect 6 48", "Damage 5 49", "Damage Type 50", "To Hit 5 51"),
    ("Removable Equipment 2 54", "Effect 7 56", "Damage 6 55", "Type 5 58", "To Hit 6 57"),
    ("Removable Equipment 3 61", None, "Damage 7 62", None, "To Hit 7 63"),
    ("Removable Equipment 4 66", "Effect 69", "Damage 8 67", None, "To Hit 8 68"),
)


def _clean(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.casefold() in {"", "nan", "none", "nat"}:
        return ""
    return text


def _normalise_key(value: object) -> str:
    return " ".join(_clean(value).casefold().split())


def _normalise_size(value: object) -> str:
    key = _normalise_key(value)
    return SIZE_ALIASES.get(key, key)


def _decimal(value: object) -> Decimal:
    """Parse a plain number, returning zero for blanks and non-numbers."""
    text = _clean(value).replace(",", "")
    if not text:
        return Decimal(0)
    text = text.lstrip("=+")
    try:
        result = Decimal(text)
    except (InvalidOperation, ValueError):
        return Decimal(0)
    return result if result.is_finite() else Decimal(0)


def _percent(value: object) -> Decimal:
    """Parse a percentage or a fraction into a Decimal fraction.

    ``50%`` and ``50.00%`` become ``0.50``.  ``0.25`` stays ``0.25`` while a
    few spreadsheet cells store ``25`` where ``0.25`` is intended.
    """
    text = _clean(value)
    if not text:
        return Decimal(0)
    text = text.lstrip("=+")
    is_percent = text.endswith("%")
    if is_percent:
        text = text[:-1].strip()
    result = _decimal(text)
    if is_percent:
        return result / Decimal(100)
    if abs(result) > 1:
        return result / Decimal(100)
    return result


def _integer(value: object, default: int = 0) -> int:
    return round_half_up(_decimal(value)) if _clean(value) else default


def round_half_up(value: Decimal) -> int:
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def format_number(value: object) -> str:
    """Format numbers without trailing ``.0`` while preserving text values."""
    if value is None:
        return ""
    if isinstance(value, Decimal):
        if not value.is_finite():
            return ""
        if value == value.to_integral_value():
            return str(int(value))
        return format(value.normalize(), "f")
    text = _clean(value)
    if not text:
        return ""
    try:
        number = Decimal(text.replace(",", ""))
    except (InvalidOperation, ValueError):
        return text
    if not number.is_finite():
        return text
    if number == number.to_integral_value():
        return str(int(number))
    return format(number.normalize(), "f")


def parse_weapon_tags(value: object) -> frozenset[str]:
    """Split a weapon/ability type field into case-insensitive tags."""
    tags: set[str] = set()
    for part in re.split(r"[,.;]", _clean(value)):
        part = part.strip().casefold()
        if not part:
            continue
        # Accommodate source values such as "Melee Piercing".
        match = re.fullmatch(r"(melee|ranged)\s+(.+)", part)
        if match:
            tags.update(match.groups())
        else:
            tags.add(part)

    aliases = {
        "anti-ait": "anti-air",
        "electric": "electrical",
        "electic": "electrical",
        "electical": "electrical",
        "lighting": "electrical",
        "freezing": "freeze",
    }
    return frozenset(aliases.get(tag, tag) for tag in tags)


def _family_and_rank(name: str) -> tuple[str, int]:
    match = re.match(r"^(.*?)\s*(\d+)\s*$", name)
    if not match:
        return name.casefold(), 1
    return match.group(1).strip().casefold(), int(match.group(2))


@dataclass(frozen=True)
class WeaponRecord:
    name: str
    effect: str
    damage: str
    damage_value: Decimal | None
    tags: frozenset[str]
    to_hit: Decimal
    has_to_hit: bool


@dataclass(frozen=True)
class ZoidRecord:
    name: str
    type: str
    size: str
    level_required: int
    health: Decimal
    armor: Decimal
    defense: Decimal
    speed: Decimal
    reaction: Decimal
    range: Decimal
    weapons: tuple[WeaponRecord, ...]
    unique_weapon: WeaponRecord | None = None


@dataclass(frozen=True)
class AbilityRecord:
    name: str
    description: str
    level_bonus: Decimal
    eligible_sizes: frozenset[str]
    all_stats: Decimal
    armor: Decimal
    to_hit: Decimal
    speed: Decimal
    range: Decimal
    reaction: Decimal
    damage_bonus: Decimal
    shield: Decimal
    equipment_defense: Decimal
    damage_tags: frozenset[str]
    base_defense: Decimal
    family: str
    rank: int
    type_bonus: str | None


@dataclass(frozen=True)
class StatsRow:
    health: Decimal
    armor: Decimal
    react: Decimal
    perception: Decimal
    to_hit: Decimal


@dataclass(frozen=True)
class WeaponStats:
    name: str
    damage: str
    to_hit: str


@dataclass(frozen=True)
class EnemyStats:
    health: str
    armor: str
    defense: str
    speed: str
    range: str
    reaction: str
    weapons: tuple[WeaponStats, ...]
    effective_level: int
    summary: str


@dataclass(frozen=True)
class EnemyData:
    zoids: dict[str, ZoidRecord]
    abilities: dict[str, AbilityRecord]
    stats: dict[str, dict[int, StatsRow]]
    zoid_names: tuple[str, ...]
    ability_names: tuple[str, ...]
    stats_type_names: tuple[str, ...]


def _weapon_from_values(
    name: object,
    effect: object,
    damage: object,
    type_value: object,
    hit: object,
) -> WeaponRecord:
    weapon_name = _clean(name)
    damage_text = format_number(damage)
    hit_text = format_number(hit)
    # Treat "no name, zero damage, zero to-hit" as an empty slot.  The JSON
    # catalog uses zeroes in some formerly empty weapon columns.
    if not weapon_name and damage_text in {"", "0"} and hit_text in {"", "0"}:
        return WeaponRecord(
            name="",
            effect="",
            damage="",
            damage_value=Decimal(0),
            tags=frozenset(),
            to_hit=Decimal(0),
            has_to_hit=False,
        )
    damage_value: Decimal | None
    try:
        damage_value = Decimal(damage_text.replace(",", "")) if damage_text else Decimal(0)
        if not damage_value.is_finite():
            damage_value = None
    except (InvalidOperation, ValueError):
        damage_value = None
    return WeaponRecord(
        name=weapon_name,
        effect=_clean(effect),
        damage=damage_text,
        damage_value=damage_value,
        tags=parse_weapon_tags(type_value),
        to_hit=_decimal(hit_text),
        has_to_hit=bool(hit_text),
    )


def _weapon_from_row(row: dict[str, str], columns: tuple[str, str, str, str, str]) -> WeaponRecord:
    name_col, effect_col, damage_col, type_col, hit_col = columns
    return _weapon_from_values(
        row.get(name_col),
        row.get(effect_col),
        row.get(damage_col),
        row.get(type_col),
        row.get(hit_col),
    )


def _field_value(fields: Mapping[str, object], key: str | None) -> object:
    return fields.get(key) if key else None


def _unique_weapon_display(name: object, effect: object) -> tuple[str, str]:
    """Return a short weapon name and its effect text.

    Some source rows put the full effect in the removable-equipment name,
    followed by a "(... Only)" marker.  Keep the name before the colon and
    move the remainder into the effect text.  Rows with an effect column
    already populated keep their clean name as-is.
    """
    name_text = _clean(name)
    effect_text = _clean(effect)
    head, separator, tail = name_text.partition(":")
    if separator and head.strip():
        name_text = f"{head.strip()}:"
        if not effect_text and tail.strip():
            effect_text = tail.strip()
    elif not separator:
        name_text = re.sub(
            r"\s*\([^)]*\bonly\b[^)]*\)\s*$",
            "",
            name_text,
            flags=re.IGNORECASE,
        ).strip()
    return name_text, effect_text


def _unique_removable_weapon(
    fields: Mapping[str, object],
    columns: Sequence[tuple[str, str | None, str, str | None, str]],
) -> WeaponRecord | None:
    """Find the Zoid-specific removable weapon embedded in a data row."""
    for name_key, effect_key, damage_key, type_key, hit_key in columns:
        name = _clean(_field_value(fields, name_key))
        effect = _clean(_field_value(fields, effect_key))
        if not name:
            continue
        if not re.search(r"\bonly\b", f"{name} {effect}", flags=re.IGNORECASE):
            continue

        damage = _field_value(fields, damage_key)
        damage_type = _field_value(fields, type_key)
        to_hit = _field_value(fields, hit_key)
        damage_text = format_number(damage)
        hit_text = format_number(to_hit)
        # Unique assists (repair units, camouflage, shields) live in the same
        # slots but have no weapon statistics, so they are not extra weapons.
        if damage_text in {"", "0"} and hit_text in {"", "0"} and not _clean(damage_type):
            continue

        display_name, display_effect = _unique_weapon_display(name, effect)
        if not display_name:
            continue
        return _weapon_from_values(
            display_name,
            display_effect,
            damage,
            damage_type,
            to_hit,
        )
    return None


def _zoid_from_json(name: str, fields: dict[str, object]) -> ZoidRecord:
    return ZoidRecord(
        name=name,
        type=_clean(fields.get("type")),
        size=_normalise_size(fields.get("size")),
        level_required=max(1, _integer(fields.get("required_level"), 1)),
        health=_decimal(fields.get("health")),
        armor=_decimal(fields.get("armor")),
        defense=_decimal(fields.get("defense")),
        speed=_decimal(fields.get("speed")),
        reaction=_decimal(fields.get("reaction")),
        range=_decimal(fields.get("range")),
        weapons=tuple(
            _weapon_from_values(
                fields.get(name_key),
                fields.get(effect_key),
                fields.get(damage_key),
                fields.get(type_key),
                fields.get(hit_key),
            )
            for name_key, effect_key, damage_key, type_key, hit_key in JSON_WEAPON_COLUMNS
        ),
        unique_weapon=_unique_removable_weapon(fields, JSON_REMOVABLE_WEAPON_COLUMNS),
    )


def _load_json_records(path: Path) -> list[dict[str, object]]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    records = payload.get("records", []) if isinstance(payload, dict) else payload
    if not isinstance(records, list):
        return []
    return [
        record
        for record in records
        if isinstance(record, dict) and isinstance(record.get("fields"), dict)
    ]


def _load_zoids(path: Path, zoids_json: Path | None = None) -> dict[str, ZoidRecord]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames:
            fieldnames = [str(name).strip() for name in reader.fieldnames]
            reader.fieldnames = fieldnames
        zoids: dict[str, ZoidRecord] = {}
        weapon_columns = (
            ("Weapon 1 13", "Effect 2 14", "Damage 1 15", "Type 1 16", "To Hit 1  17"),
            ("Weapon 2 19", "Effect 3 20", "Damage 2  21", "Type 2 22", "To Hit 2  23"),
            ("Weapon 3 30", "Effect 4 31", "Damage 3 32", "Type 3 33", "To Hit 3 34"),
            ("Weapon 4 41", "Effect 5 42", "Damage 4 43", "Type 4 44", "To Hit 4 45"),
        )
        for row in reader:
            name = _clean(row.get("Name 1"))
            if not name:
                continue
            zoids[name] = ZoidRecord(
                name=name,
                type=_clean(row.get("Type 3")),
                size=_normalise_size(row.get("Size 4")),
                level_required=max(1, _integer(row.get("Level Required 5"), 1)),
                health=_decimal(row.get("Health 6")),
                armor=_decimal(row.get("Armor 7")),
                defense=_decimal(row.get("Defense 8")),
                speed=_decimal(row.get("Speed 9")),
                reaction=_decimal(row.get("Reaction 10")),
                range=_decimal(row.get("Range 11")),
                weapons=tuple(_weapon_from_row(row, columns) for columns in weapon_columns),
                unique_weapon=_unique_removable_weapon(row, CSV_REMOVABLE_WEAPON_COLUMNS),
            )

    if zoids_json is None or not Path(zoids_json).is_file():
        return zoids

    records = _load_json_records(Path(zoids_json))
    json_by_name: dict[str, dict[str, object]] = {}
    for record in records:
        fields = record["fields"]
        json_name = _clean(fields.get("name"))
        aliases = [json_name, *(record.get("legacy_names") or [])]
        for alias in aliases:
            key = _normalise_key(alias)
            if key:
                json_by_name.setdefault(key, record)

    for csv_key, json_key in CSV_TO_JSON_NAME_OVERRIDES.items():
        record = json_by_name.get(_normalise_key(json_key))
        if record is not None:
            json_by_name[_normalise_key(csv_key)] = record

    csv_by_key = {_normalise_key(name): name for name in zoids}
    for key, record in json_by_name.items():
        csv_name = csv_by_key.get(key)
        if csv_name is None:
            continue
        fields = record["fields"]
        zoids[csv_name] = _zoid_from_json(csv_name, fields)
    return zoids


def _load_stats(path: Path) -> dict[str, dict[int, StatsRow]]:
    blocks: list[dict[int, StatsRow]] = []
    current: dict[int, StatsRow] | None = None
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.reader(handle):
            if not row:
                continue
            first = _clean(row[0]) if row else ""
            if not first:
                continue
            if first.casefold() == "level":
                current = {}
                blocks.append(current)
                continue
            if current is None or len(row) < 6:
                continue
            level = _integer(row[0], -1)
            if level < 1:
                continue
            current[level] = StatsRow(
                health=_percent(row[1]),
                armor=_percent(row[2]),
                react=_percent(row[3]),
                perception=_percent(row[4]),
                to_hit=_percent(row[5]),
            )

    stats: dict[str, dict[int, StatsRow]] = {}
    for index, block in enumerate(blocks):
        if not block:
            continue
        name = STATS_TYPE_NAMES[index] if index < len(STATS_TYPE_NAMES) else f"Block {index + 1}"
        stats[name] = block
    return stats


def _type_bonus_candidates(zoid_type: str) -> tuple[str, ...]:
    """Return source spellings that refer to a catalog Zoid type."""
    candidates = [zoid_type]
    if _normalise_key(zoid_type) == "liger":
        # The ability CSV still uses the older Lion terminology.
        candidates.append("Lion")
    return tuple(candidates)


def _load_abilities(path: Path, zoid_types: Iterable[str]) -> dict[str, AbilityRecord]:
    type_list = sorted({_clean(value) for value in zoid_types if _clean(value)}, key=len, reverse=True)
    abilities: dict[str, AbilityRecord] = {}
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames:
            fieldnames = [str(name).strip() for name in reader.fieldnames]
            reader.fieldnames = fieldnames
        for row in reader:
            name = _clean(row.get("Skills 1"))
            if not name or name.startswith("- - -"):
                continue
            description = _clean(row.get("Descriptions 2"))
            level_bonus = _decimal(row.get("Levels 3"))
            type_bonus = None
            name_lower = name.casefold()
            if level_bonus != 0 and "type" in name_lower:
                for zoid_type in type_list:
                    for prefix_value in _type_bonus_candidates(zoid_type):
                        prefix = prefix_value.casefold()
                        if name_lower.startswith(prefix) and re.match(
                            rf"^{re.escape(prefix)}\s*type\b", name_lower
                        ):
                            type_bonus = zoid_type
                            break
                    if type_bonus is not None:
                        break
            family, rank = _family_and_rank(name)
            abilities[name] = AbilityRecord(
                name=name,
                description=description,
                level_bonus=level_bonus,
                eligible_sizes=frozenset(
                    _normalise_size(part)
                    for part in _clean(row.get("If in Zoid Size 4")).split(",")
                    if _clean(part)
                ),
                all_stats=_percent(row.get("All Stats 5")),
                armor=_percent(row.get("Armor 6")),
                to_hit=_decimal(row.get("To Hit Increase 7")),
                speed=_decimal(row.get("Speed 8")),
                range=_decimal(row.get("Range 9")),
                reaction=_decimal(row.get("Reaction 10")),
                damage_bonus=_percent(row.get("Damage Bonus 11")),
                shield=_decimal(row.get("Shield Increase 12")),
                equipment_defense=_decimal(row.get("Equiped Defense 13")),
                damage_tags=parse_weapon_tags(row.get("Damage Type 14")),
                base_defense=_decimal(row.get("Zoids base Defense 15")),
                family=family,
                rank=rank,
                type_bonus=type_bonus,
            )
    return abilities


def load_enemy_data(
    zoids_csv: str | Path,
    stats_csv: str | Path,
    abilities_csv: str | Path,
    zoids_json: str | Path | None = None,
) -> EnemyData:
    zoids = _load_zoids(
        Path(zoids_csv),
        Path(zoids_json) if zoids_json is not None else None,
    )
    stats = _load_stats(Path(stats_csv))
    abilities = _load_abilities(Path(abilities_csv), (zoid.type for zoid in zoids.values()))
    return EnemyData(
        zoids=zoids,
        abilities=abilities,
        stats=stats,
        zoid_names=tuple(sorted(zoids, key=str.casefold)),
        ability_names=tuple(sorted(abilities, key=str.casefold)),
        stats_type_names=tuple(name for name in STATS_TYPE_NAMES if name in stats),
    )


def _selected_abilities(
    ability_names: Sequence[str], abilities: dict[str, AbilityRecord]
) -> list[AbilityRecord]:
    """Keep the highest selected rank of each ability family."""
    selected: list[AbilityRecord] = []
    seen: dict[str, AbilityRecord] = {}
    for name in ability_names:
        record = abilities.get(name)
        if record is None:
            continue
        current = seen.get(record.family)
        if current is None:
            seen[record.family] = record
            selected.append(record)
        elif record.rank > current.rank:
            selected[selected.index(current)] = record
            seen[record.family] = record
    return selected


def _weapon_expert_bonus(weapon: WeaponRecord, abilities: Sequence[AbilityRecord]) -> Decimal:
    applicable: list[AbilityRecord] = []
    for ability in abilities:
        if ability.to_hit == 0 or not ability.damage_tags:
            continue
        family = ability.family
        # The ability CSV uses the older Energy/Piercing wording.  The
        # Character Sheet catalog uses Laser/Bullet in weapon tags.
        if "laser expert" in family:
            if "ranged" not in weapon.tags or "melee" in weapon.tags:
                continue
            if not (weapon.tags & {"laser", "energy"}):
                continue
            applicable.append(ability)
            continue
        if "rifle expert" in family:
            if "ranged" in weapon.tags and (weapon.tags & {"bullet", "piercing"}):
                applicable.append(ability)
            continue
        if ability.damage_tags.issubset(weapon.tags):
            applicable.append(ability)

    strongest = max(
        (ability.to_hit for ability in applicable if "anti-air pro" not in ability.family),
        default=Decimal(0),
    )
    anti_air = sum(
        (ability.to_hit for ability in applicable if "anti-air pro" in ability.family),
        Decimal(0),
    )
    return strongest + anti_air


def _summary(
    zoid: ZoidRecord,
    stats_type: str,
    base_level: int,
    effective_level: int,
    bonus_levels: Decimal,
    size_bonus: Decimal,
    selected: Sequence[AbilityRecord],
) -> str:
    notes: list[str] = []
    if stats_type:
        level_note = f"{stats_type} · effective level {effective_level}"
        if bonus_levels:
            level_note += f" ({base_level} + {format_number(bonus_levels)} from type ability)"
        notes.append(level_note)
    else:
        notes.append("No Stats type selected")
    if size_bonus:
        notes.append(f"Size bonus +{format_number(size_bonus * 100)}%")
    flat_parts = []
    defense = sum((a.base_defense for a in selected), Decimal(0))
    speed = sum((a.speed for a in selected), Decimal(0))
    reaction = sum((a.reaction for a in selected), Decimal(0))
    range_bonus = sum((a.range for a in selected), Decimal(0))
    if defense:
        flat_parts.append(f"{format_number(defense)} Defense")
    if speed:
        flat_parts.append(f"{format_number(speed)} Speed")
    if reaction:
        flat_parts.append(f"{format_number(reaction)} Reaction")
    if range_bonus:
        flat_parts.append(f"{format_number(range_bonus)} Range")
    if flat_parts:
        notes.append("Flat: " + ", ".join(flat_parts))
    if any(a.damage_bonus for a in selected):
        notes.append("Comeback damage applies only at 20% HP or less")
    return " · ".join(notes)


def calculate_enemy_stats(
    zoid: ZoidRecord,
    level: object,
    stats_type: str | None,
    ability_names: Sequence[str],
    data: EnemyData,
) -> EnemyStats:
    """Apply a Stats table and selected abilities to a Zoid's base values."""
    selected = _selected_abilities(ability_names, data.abilities)

    base_level = max(1, _integer(level, zoid.level_required or 1))
    zoid_type_key = _normalise_key(zoid.type)
    bonus_levels = max(
        (
            ability.level_bonus
            for ability in selected
            if ability.type_bonus
            and (
                _normalise_key(ability.type_bonus) == zoid_type_key
                or (
                    _normalise_key(ability.type_bonus) == "liger"
                    and zoid_type_key == "lion"
                )
            )
        ),
        default=Decimal(0),
    )
    effective_level = base_level + int(bonus_levels)

    progression: StatsRow | None = None
    normalised_type = next(
        (name for name in data.stats if name.casefold() == _clean(stats_type).casefold()),
        None,
    )
    if normalised_type:
        table = data.stats[normalised_type]
        if table:
            lookup_level = min(max(effective_level, min(table)), max(table))
            progression = table.get(lookup_level)

    health_percent = progression.health if progression else Decimal(0)
    armor_percent = progression.armor if progression else Decimal(0)
    react_percent = progression.react if progression else Decimal(0)
    perception_percent = progression.perception if progression else Decimal(0)
    to_hit_percent = progression.to_hit if progression else Decimal(0)

    matching_size = next(
        (ability for ability in selected if zoid.size in ability.eligible_sizes),
        None,
    )
    size_bonus = matching_size.all_stats if matching_size else Decimal(0)

    # This mirrors the reference calculation: armor percentage abilities are
    # only part of the armor formula when a matching size ability is active.
    armor_ability_percent = (
        sum((ability.armor for ability in selected), Decimal(0)) if matching_size else Decimal(0)
    )
    base_defense_bonus = sum((ability.base_defense for ability in selected), Decimal(0))
    speed_bonus = sum((ability.speed for ability in selected), Decimal(0))
    reaction_bonus = sum((ability.reaction for ability in selected), Decimal(0))
    range_bonus = sum((ability.range for ability in selected), Decimal(0))

    health = round_half_up(zoid.health * (1 + health_percent + size_bonus))
    armor = round_half_up(
        zoid.armor * (1 + armor_percent + size_bonus + armor_ability_percent)
    )
    defense = round_half_up(zoid.defense + base_defense_bonus)
    speed = round_half_up(zoid.speed + speed_bonus)
    reaction = round_half_up(zoid.reaction * (1 + react_percent + size_bonus)) + round_half_up(reaction_bonus)
    # The reference calculation leaves Range unrounded, allowing a .5 result.
    range_value = zoid.range * (1 + perception_percent + size_bonus) + range_bonus

    weapon_stats: list[WeaponStats] = []
    weapons = zoid.weapons + ((zoid.unique_weapon,) if zoid.unique_weapon else ())
    for weapon in weapons:
        if not weapon.has_to_hit and not weapon.name and not weapon.damage:
            weapon_stats.append(WeaponStats(name="", damage="", to_hit=""))
            continue
        if weapon.has_to_hit:
            expert_bonus = _weapon_expert_bonus(weapon, selected)
            to_hit = round_half_up(
                weapon.to_hit * (1 + to_hit_percent + size_bonus) + expert_bonus
            )
            to_hit_text = str(to_hit)
        else:
            to_hit_text = ""
        weapon_stats.append(
            WeaponStats(
                name=weapon.name,
                damage=format_number(weapon.damage),
                to_hit=to_hit_text,
            )
        )

    normalised_stats_type = normalised_type or ""
    summary = _summary(
        zoid=zoid,
        stats_type=normalised_stats_type,
        base_level=base_level,
        effective_level=effective_level,
        bonus_levels=bonus_levels,
        size_bonus=size_bonus,
        selected=selected,
    )
    return EnemyStats(
        health=str(health),
        armor=str(armor),
        defense=str(defense),
        speed=str(speed),
        range=format_number(range_value),
        reaction=str(reaction),
        weapons=tuple(weapon_stats),
        effective_level=effective_level,
        summary=summary,
    )
