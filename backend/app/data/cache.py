import json
from pathlib import Path
from typing import Any


BACKEND_ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = BACKEND_ROOT / "cache"
DEMO_DIR = BACKEND_ROOT / "demo"


def location_key(lat: float, lon: float, precision: int = 2) -> str:
    return f"{round(lat, precision):.2f}_{round(lon, precision):.2f}"


def cache_path(namespace: str, lat: float, lon: float) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / f"{namespace}_{location_key(lat, lon)}.json"


def read_cache(namespace: str, lat: float, lon: float) -> dict[str, Any] | None:
    path = cache_path(namespace, lat, lon)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def write_cache(namespace: str, lat: float, lon: float, payload: dict[str, Any]) -> None:
    path = cache_path(namespace, lat, lon)
    try:
        path.write_text(json.dumps(payload), encoding="utf-8")
    except OSError:
        pass


def read_demo_json(filename: str) -> dict[str, Any]:
    path = DEMO_DIR / filename
    return json.loads(path.read_text(encoding="utf-8"))
