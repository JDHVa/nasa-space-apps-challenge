import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from app.data.farms import FARMS, load_farm_site
from app.schemas import Site, Soil
from app.twin.crops import CROPS, FALLOW
from app.twin.engine import SampleWeather
from app.twin.ensemble import METRIC_UNITS, SiteParams, build_samples, run_strategy
from app.twin.rotations import generate_alternatives

MODEL_PATH = Path(__file__).resolve().parents[2] / "models" / "emulator.pt"
META_PATH = MODEL_PATH.with_suffix(".json")
METRIC_KEYS: list[str] = list(METRIC_UNITS.keys())
CROP_VOCAB: list[str] = ["none", FALLOW] + sorted(CROPS)
SLOTS = 3
YEARS = 5
MEMBERS = 5
CONFIDENCE = 0.9
IRRIGATION_RANGE = (0.0, 300.0)
WARMING_RANGE = (0.0, 2.5)
NUMERIC_NAMES = ["shift", "irrigation", "warming", "precip", "et0", "tmax", "tmin", "slope", "sm", "awc", "cn", "k", "wp"]
RANGE_MARGIN = 0.15


@dataclass
class Prediction:
    p50: dict[str, float]
    quantile: dict[str, float]
    coverage: float


def encode_crops(crops: list[str]) -> np.ndarray:
    out = np.zeros(SLOTS * len(CROP_VOCAB), dtype=np.float32)
    padded = (list(crops) + ["none"] * SLOTS)[:SLOTS]
    for slot, name in enumerate(padded):
        out[slot * len(CROP_VOCAB) + CROP_VOCAB.index(name)] = 1.0
    return out


def numeric_features(*values: float) -> np.ndarray:
    return np.array(values, dtype=np.float32)


def climate_of(samples: SampleWeather) -> tuple[float, float, float, float]:
    years = samples.precip.shape[0] / 365
    return (
        float(samples.precip.sum(axis=0).mean() / years),
        float(samples.et0.sum(axis=0).mean() / years),
        float(samples.tmax.mean()),
        float(samples.tmin.mean()),
    )


def shifted(samples: SampleWeather, delta: np.ndarray, precip_factor: np.ndarray, warming: np.ndarray) -> SampleWeather:
    tmax = samples.tmax + delta
    tmin = samples.tmin + delta
    return SampleWeather(
        tmax, tmin, samples.precip * precip_factor, samples.et0_for(tmax, tmin), warming,
        samples.srad, samples.rh, samples.ws, samples.lat, samples.elevation,
    )


def without_warming(samples: SampleWeather) -> SampleWeather:
    shift = samples.warming[None, :]
    return shifted(samples, -shift, 1.0 / (1.0 - 0.02 * shift), np.zeros(samples.tmax.shape[1]))


def with_warming(samples: SampleWeather, warming: float) -> SampleWeather:
    return shifted(samples, warming, 1.0 - 0.02 * warming, np.full(samples.tmax.shape[1], warming))


def random_soil(base: Soil, rng: np.random.Generator) -> Soil:
    if rng.random() < 0.5:
        return base
    awc = base.awc_mm_per_m * float(rng.uniform(0.7, 1.3))
    wilting = float(np.clip(base.wilting_point + rng.uniform(-0.04, 0.04), 0.05, 0.3))
    return base.model_copy(
        update={
            "awc_mm_per_m": awc,
            "wilting_point": wilting,
            "field_capacity": wilting + awc / 1000.0,
            "curve_number": float(np.clip(base.curve_number + rng.uniform(-6, 6), 70, 96)),
            "k_factor": float(np.clip(base.k_factor * rng.uniform(0.7, 1.3), 0.05, 0.5)),
        }
    )


def random_crops(rng: np.random.Generator) -> list[str]:
    names = sorted(CROPS)
    if rng.random() < 0.3:
        base = [str(n) for n in rng.choice(names, size=int(rng.integers(1, 3)))]
        plans = [list(p.crops) for p in generate_alternatives(base)]
        return plans[int(rng.integers(0, len(plans)))] if plans else base
    size = int(rng.integers(1, SLOTS + 1))
    pool = names + [FALLOW]
    crops = [str(pool[int(rng.integers(0, len(pool)))]) for _ in range(size)]
    if all(c == FALLOW for c in crops):
        crops[0] = str(names[int(rng.integers(0, len(names)))])
    if rng.random() < 0.2:
        crops[0] = str(names[int(rng.integers(0, len(names)))])
    return crops


def build_dataset(count: int, seed: int = 11) -> tuple[np.ndarray, np.ndarray]:
    farms = [load_farm_site(name) for name in FARMS]
    rng = np.random.default_rng(seed)
    features: list[np.ndarray] = []
    targets: list[list[float]] = []
    for _ in range(count):
        data = farms[int(rng.integers(0, len(farms)))]
        frost_days = float((data.weather.tmin < 0).sum() / data.weather.tmin.shape[0])
        crops = random_crops(rng)
        shift = float(rng.integers(-30, 31))
        irrigation = float(rng.uniform(*IRRIGATION_RANGE)) if rng.random() < 0.8 else 0.0
        warming = float(rng.uniform(*WARMING_RANGE))
        slope = float(rng.uniform(0.3, 9.0))
        soil = random_soil(data.soil, rng)
        sm = soil.wilting_point + float(rng.uniform(0.1, 0.9)) * (soil.field_capacity - soil.wilting_point)
        samples = build_samples(data.weather, data.lat, YEARS, MEMBERS, seed=int(rng.integers(0, 1_000_000)), elevation=data.gee.elevation_m)
        samples = without_warming(samples)
        precip, et0, tmax, tmin = climate_of(samples)
        samples = with_warming(samples, warming)
        run = run_strategy(crops, samples, SiteParams(data.lat, slope, sm, soil, frost_days), YEARS, irrigation, int(shift))
        numeric = numeric_features(
            shift, irrigation, warming, precip, et0, tmax, tmin, slope, sm,
            soil.awc_mm_per_m, soil.curve_number, soil.k_factor, soil.wilting_point,
        )
        features.append(np.concatenate([encode_crops(crops), numeric]))
        targets.append([float(np.median(run.metrics[key])) for key in METRIC_KEYS])
    return np.stack(features), np.array(targets, dtype=np.float32)


def build_network(inputs: int, outputs: int):
    import torch.nn as nn

    return nn.Sequential(
        nn.Linear(inputs, 256), nn.SiLU(),
        nn.Linear(256, 256), nn.SiLU(),
        nn.Linear(256, 128), nn.SiLU(),
        nn.Linear(128, outputs),
    )


def train(count: int = 4000, epochs: int = 400, seed: int = 3) -> dict:
    import torch

    started = time.time()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    features, targets = build_dataset(count)
    build_seconds = time.time() - started
    order = np.random.default_rng(seed).permutation(count)
    n_train, n_cal = int(count * 0.7), int(count * 0.15)
    train_idx, cal_idx, test_idx = order[:n_train], order[n_train : n_train + n_cal], order[n_train + n_cal :]
    crop_width = SLOTS * len(CROP_VOCAB)
    num_mean = features[train_idx, crop_width:].mean(axis=0)
    num_std = features[train_idx, crop_width:].std(axis=0) + 1e-6
    y_mean = targets[train_idx].mean(axis=0)
    y_std = targets[train_idx].std(axis=0) + 1e-6

    scaled = features.copy()
    scaled[:, crop_width:] = (scaled[:, crop_width:] - num_mean) / num_std
    torch.manual_seed(seed)
    x_all = torch.tensor(scaled, dtype=torch.float32, device=device)
    y_all = torch.tensor((targets - y_mean) / y_std, dtype=torch.float32, device=device)
    network = build_network(x_all.shape[1], y_all.shape[1]).to(device)
    optimizer = torch.optim.AdamW(network.parameters(), lr=2e-3, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
    train_t = torch.tensor(train_idx, device=device)
    batch = 256
    for _ in range(epochs):
        network.train()
        perm = train_t[torch.randperm(len(train_t), device=device)]
        for start in range(0, len(perm), batch):
            chunk = perm[start : start + batch]
            optimizer.zero_grad()
            loss = torch.nn.functional.smooth_l1_loss(network(x_all[chunk]), y_all[chunk], beta=0.5)
            loss.backward()
            optimizer.step()
        scheduler.step()
    network.eval()
    with torch.no_grad():
        pred = network(x_all).cpu().numpy() * y_std + y_mean
    cal_res = np.abs(pred[cal_idx] - targets[cal_idx])
    level = min(1.0, np.ceil((len(cal_idx) + 1) * CONFIDENCE) / len(cal_idx))
    quantiles = np.quantile(cal_res, level, axis=0)
    test_res = np.abs(pred[test_idx] - targets[test_idx])
    coverage = (test_res <= quantiles).mean(axis=0)
    truth = targets[test_idx]
    ss_res = ((pred[test_idx] - truth) ** 2).sum(axis=0)
    ss_tot = ((truth - truth.mean(axis=0)) ** 2).sum(axis=0) + 1e-9
    r2 = 1.0 - ss_res / ss_tot
    ranges = {
        name: [float(features[:, crop_width + i].min()), float(features[:, crop_width + i].max())]
        for i, name in enumerate(NUMERIC_NAMES)
    }
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "state": {k: v.cpu() for k, v in network.state_dict().items()},
            "num_mean": num_mean, "num_std": num_std, "y_mean": y_mean, "y_std": y_std,
            "quantiles": quantiles, "coverage": float(coverage.mean()), "ranges": ranges,
        },
        MODEL_PATH,
    )
    meta = {
        "device": str(device), "samples": count, "epochs": epochs, "metrics": METRIC_KEYS,
        "test_r2": {k: round(float(v), 4) for k, v in zip(METRIC_KEYS, r2)},
        "test_coverage": {k: round(float(v), 4) for k, v in zip(METRIC_KEYS, coverage)},
        "mean_test_coverage": round(float(coverage.mean()), 4),
        "conformal_quantiles": {k: round(float(v), 4) for k, v in zip(METRIC_KEYS, quantiles)},
        "ranges": ranges, "dataset_seconds": round(build_seconds, 1), "total_seconds": round(time.time() - started, 1),
    }
    META_PATH.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta


class Emulator:
    def __init__(self, bundle: dict) -> None:
        import torch

        self.bundle = bundle
        width = bundle["state"]["0.weight"].shape[1]
        self.network = build_network(width, len(METRIC_KEYS))
        self.network.load_state_dict(bundle["state"])
        self.network.eval()
        self.torch = torch

    def in_range(self, values: dict[str, float]) -> bool:
        for name, value in values.items():
            low, high = self.bundle["ranges"][name]
            margin = RANGE_MARGIN * max(high - low, 1e-6)
            if value < low - margin or value > high + margin:
                return False
        return True

    def predict(self, crops: list[str], shift: float, irrigation: float, warming: float, site: Site, soil: Soil) -> Prediction | None:
        if any(c not in CROP_VOCAB for c in crops) or len(crops) > SLOTS:
            return None
        climate = site.climate
        values = {
            "shift": shift, "irrigation": irrigation, "warming": warming,
            "precip": climate.precip_annual_mm, "et0": climate.et0_annual_mm,
            "tmax": climate.tmax_mean, "tmin": climate.tmin_mean,
            "slope": site.slope_deg, "sm": site.sm_rootzone,
            "awc": soil.awc_mm_per_m, "cn": soil.curve_number, "k": soil.k_factor, "wp": soil.wilting_point,
        }
        if not self.in_range(values):
            return None
        numeric = numeric_features(*[values[n] for n in NUMERIC_NAMES])
        numeric = (numeric - self.bundle["num_mean"]) / self.bundle["num_std"]
        row = np.concatenate([encode_crops(crops), numeric.astype(np.float32)])[None, :]
        with self.torch.no_grad():
            raw = self.network(self.torch.tensor(row, dtype=self.torch.float32)).numpy()[0]
        pred = raw * self.bundle["y_std"] + self.bundle["y_mean"]
        quantile = self.bundle["quantiles"]
        return Prediction(
            {k: float(pred[i]) for i, k in enumerate(METRIC_KEYS)},
            {k: float(quantile[i]) for i, k in enumerate(METRIC_KEYS)},
            float(self.bundle["coverage"]),
        )


_STATE: dict[str, Emulator | None] = {}


def get_emulator() -> Emulator | None:
    if "emulator" not in _STATE:
        try:
            import torch

            _STATE["emulator"] = Emulator(torch.load(MODEL_PATH, map_location="cpu", weights_only=False)) if MODEL_PATH.exists() else None
        except Exception:
            _STATE["emulator"] = None
    return _STATE["emulator"]


def reset_emulator() -> None:
    _STATE.clear()


def main() -> None:
    command = sys.argv[1] if len(sys.argv) > 1 else "train"
    if command != "train":
        raise SystemExit("usage: python -m app.ai.emulator train [samples]")
    count = min(int(sys.argv[2]), 4000) if len(sys.argv) > 2 else 4000
    print(json.dumps(train(count), indent=2))


if __name__ == "__main__":
    main()
