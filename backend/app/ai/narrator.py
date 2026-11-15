import json
import re
import time
from typing import Callable, Iterator

from app.schemas import AnalyzeResponse, Strategy

OLLAMA_HOST = "http://localhost:11434"
OLLAMA_MODEL = "qwen3:4b-instruct-2507-q4_K_M"
TOTAL_TIMEOUT_S = 60.0

SYSTEM_PROMPT = (
    "You are an agronomy decision-support explainer for a farm digital twin. Write exactly 4 short paragraphs, "
    "each starting with its label on its own: "
    "'Why consider it:' (1-2 sentences on the idea behind this strategy), "
    "'What the twin shows:' (compare against the current rotation using 3 or 4 key P50 numbers from metrics, each with its P10-P90 range and unit), "
    "'Trade-offs & risks:' (what gets worse or is uncertain, from risks and metrics), "
    "'Check locally:' (data gaps and what a local agronomist should verify). "
    "Use only numbers that appear in the provided JSON, rounded sensibly, always with units. "
    "Never write percentages unless the JSON contains them; never invent figures such as risk scores. "
    "Do not prescribe or give orders; describe what the model suggests. Answer in {language}. "
    "Maximum 170 words. Plain text only, no markdown, no bullet lists."
)
LANGUAGES = {"en": "English", "es": "Spanish"}


def build_payload(strategy: Strategy, analysis: AnalyzeResponse) -> dict:
    current = next((s for s in analysis.strategies if s.is_current), None)
    site = analysis.site
    return {
        "strategy": {
            "name": strategy.name,
            "rotation": [f"{s.crop} y{s.year_index}" for s in strategy.rotation],
            "score": strategy.score,
            "metrics": {k: {"p10": b.p10, "p50": b.p50, "p90": b.p90, "unit": b.unit} for k, b in strategy.metrics.items()},
            "why": strategy.why,
            "evidence": strategy.evidence,
            "benefits": strategy.benefits,
            "gaps": strategy.gaps,
            "risks": strategy.risks,
        },
        "current_strategy_metrics_p50": {k: b.p50 for k, b in current.metrics.items()} if current else {},
        "site": {
            "lat": site.lat, "lon": site.lon, "elevation_m": site.elevation_m, "slope_deg": site.slope_deg,
            "data_mode": site.data_mode, **site.climate.model_dump(),
        },
    }


NUMBER = re.compile(r"(?<![\w.])-?\d+(?:\.\d+)?|\d+(?:\.\d+)?")


def _payload_numbers(value: object, found: set[float]) -> None:
    if isinstance(value, bool):
        return
    if isinstance(value, (int, float)):
        found.add(float(value))
    elif isinstance(value, str):
        found.update(float(m) for m in NUMBER.findall(value))
    elif isinstance(value, dict):
        for item in value.values():
            _payload_numbers(item, found)
    elif isinstance(value, list):
        for item in value:
            _payload_numbers(item, found)


def numbers_grounded(text: str, payload: dict) -> bool:
    allowed: set[float] = set()
    _payload_numbers(payload, allowed)
    pool = set(allowed)
    for number in allowed:
        pool.update((float(round(number)), round(number, 1), round(number, 2)))
    for match in NUMBER.finditer(text):
        value = float(match.group())
        if value in (10.0, 50.0, 90.0) and match.start() > 0 and text[match.start() - 1] == "P":
            continue
        if value in pool:
            continue
        if any(abs(value - p) < 1e-9 or round(value, 1) == round(p, 1) for p in pool):
            continue
        return False
    return True


def ollama_chunks(messages: list[dict]) -> Iterator[str]:
    import ollama

    client = ollama.Client(host=OLLAMA_HOST, timeout=TOTAL_TIMEOUT_S)
    stream = client.chat(model=OLLAMA_MODEL, messages=messages, stream=True, options={"temperature": 0.3, "num_predict": 400})
    for part in stream:
        yield part["message"]["content"]


def stream_narration(
    strategy: Strategy,
    analysis: AnalyzeResponse,
    lang: str,
    fallback_text: str,
    chunk_source: Callable[[list[dict]], Iterator[str]] | None = None,
) -> Iterator[str]:
    payload = build_payload(strategy, analysis)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT.format(language=LANGUAGES.get(lang, "English"))},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False, separators=(",", ":"))},
    ]
    deadline = time.monotonic() + TOTAL_TIMEOUT_S
    pieces: list[str] = []
    try:
        for piece in (chunk_source or ollama_chunks)(messages):
            if time.monotonic() > deadline:
                break
            if piece:
                pieces.append(piece)
    except Exception:
        pass
    text = "".join(pieces)
    if text.strip() and numbers_grounded(text, payload):
        yield text
        return
    for line in fallback_text.splitlines(keepends=True):
        yield line
