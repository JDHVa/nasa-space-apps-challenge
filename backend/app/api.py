from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app import service
from app.ai import narrator
from app.schemas import AnalyzeRequest, AnalyzeResponse, ExplainRequest, WhatIfRequest, WhatIfResponse


class HealthResponse(BaseModel):
    status: str
    service: str


app = FastAPI(title="FieldTwin API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    return HealthResponse(status="ok", service="fieldtwin")


@app.post("/analyze", response_model=AnalyzeResponse)
def post_analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    return service.analyze(request)


@app.get("/demo", response_model=AnalyzeResponse)
def get_demo(farm: Literal["iowa", "bajio"] = "iowa") -> AnalyzeResponse:
    return service.get_demo(farm)


@app.post("/whatif", response_model=WhatIfResponse)
def post_whatif(request: WhatIfRequest) -> WhatIfResponse:
    return service.what_if(request)


@app.post("/explain")
def post_explain(request: ExplainRequest) -> StreamingResponse:
    match = next((s for s in request.analysis.strategies if s.id == request.strategy_id), None)
    if match is None:
        raise HTTPException(status_code=404, detail="strategy not found")
    fallback = service.explain_text(match, request.lang)
    return StreamingResponse(
        narrator.stream_narration(match, request.analysis, request.lang, fallback),
        media_type="text/plain; charset=utf-8",
    )
