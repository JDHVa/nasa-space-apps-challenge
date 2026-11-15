import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
BACKEND_DEMO = ROOT / "backend" / "demo"
FRONTEND_DATA = ROOT / "frontend" / "src" / "data"
SATELLITE_MARKERS = ("SMAP", "MODIS", "GRACE", "IMERG", "SRTM")


@pytest.mark.parametrize("farm", ["iowa", "bajio"])
def test_frontend_demo_copy_is_byte_equal(farm):
    backend_bytes = (BACKEND_DEMO / f"demo_{farm}.json").read_bytes()
    assert backend_bytes == (FRONTEND_DATA / f"demo_{farm}.json").read_bytes()


def test_default_frontend_demo_is_iowa():
    assert (FRONTEND_DATA / "demo.json").read_bytes() == (BACKEND_DEMO / "demo_iowa.json").read_bytes()


@pytest.mark.parametrize("farm", ["iowa", "bajio"])
def test_no_satellite_sources_without_satellite_data(farm):
    payload = json.loads((BACKEND_DEMO / f"demo_{farm}.json").read_text(encoding="utf-8"))
    site = payload["site"]
    if site["satellite_available"]:
        return
    assert site["gpm_annual_mm"] is None
    assert site["grace_lwe_cm"] is None
    for source in payload["sources"]:
        text = f"{source['name']} {source['dataset']}".upper()
        assert not any(marker in text for marker in SATELLITE_MARKERS)
