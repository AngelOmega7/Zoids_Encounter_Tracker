from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

ZOIDS_JSON = BASE_DIR / "zoids.json"
LOOT_JSON = BASE_DIR / "loot.json"
STATS_JSON = BASE_DIR / "stats.json"
ABILITIES_JSON = BASE_DIR / "abilities.json"
ENCOUNTERS_JSON = BASE_DIR / "encounters.json"


def validate_catalog(path: Path) -> Path:
    if not path.is_file():
        raise FileNotFoundError(
            f"Database file not found: {path.name}"
        )
    return path
