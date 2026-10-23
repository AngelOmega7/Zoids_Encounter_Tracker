from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

ZOIDS_CSV = BASE_DIR / "ZoidsDB.csv"
LOOT_CSV = BASE_DIR / "LootDB.csv"


def validate_csv(path: Path) -> Path:
    if not path.is_file():
        raise FileNotFoundError(
            f"Database file not found: {path.name}"
        )
    return path
