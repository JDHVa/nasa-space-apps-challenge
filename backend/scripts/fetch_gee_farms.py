import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.data.farms import FARMS
from app.data.gee import _env_project, fetch_live_summary

RAW = BACKEND / "data_raw"


def main() -> int:
    project = _env_project()
    if not project:
        print("GEE_PROJECT is not set (env var or .env)")
        return 1
    import ee

    ee.Initialize(project=project)
    failures = 0
    for farm, (lat, lon) in FARMS.items():
        try:
            summary = fetch_live_summary(ee, lat, lon)
        except Exception as exc:
            failures += 1
            print(f"{farm}: failed: {type(exc).__name__}: {exc}")
            continue
        target = RAW / farm / "gee.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(summary.model_dump(), indent=1), encoding="utf-8")
        print(f"{farm}: saved {target}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
