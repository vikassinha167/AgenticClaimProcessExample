from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi_mcp import FastApiMCP
from fastapi.middleware.cors import CORSMiddleware
from app.mcp.policies import DEFAULT_POLICY
from app.mcp.schemas import FraudScoreRequest, FraudScoreResponse, PolicyBundle

app = FastAPI(title="MCP Policy Server", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/policies", response_model=PolicyBundle)
def get_policies() -> PolicyBundle:
    return DEFAULT_POLICY


@app.get("/constraints")
def get_constraints() -> JSONResponse:
    constraints = {
        "allowed_procedures": DEFAULT_POLICY.allowed_procedures,
        "max_line_item_amount": DEFAULT_POLICY.max_line_item_amount,
        "exceptions": DEFAULT_POLICY.exceptions,
    }
    return JSONResponse(content=constraints)


@app.get("/allowed-procedures")
def get_allowed_procedures() -> JSONResponse:
    return JSONResponse(content={"allowed_procedures": DEFAULT_POLICY.allowed_procedures})


@app.post("/fraud-score", response_model=FraudScoreResponse)
def fraud_score(request: FraudScoreRequest) -> FraudScoreResponse:
    patterns: list[str] = []
    score = 0.05

    for item in request.items:
        procedure_code = item.procedure_code or ""
        provider = item.provider or ""
        amount = float(item.amount or 0.0)

        if procedure_code and procedure_code not in DEFAULT_POLICY.allowed_procedures:
            score += 0.35
            patterns.append("disallowed_procedure")

        if amount > DEFAULT_POLICY.max_line_item_amount:
            score += 0.25
            patterns.append("high_line_item_amount")

        if provider in DEFAULT_POLICY.exceptions.get("providers", []):
            score += 0.20
            patterns.append("exception_provider")

        if procedure_code and procedure_code.startswith("A0"):
            score += 0.10
            patterns.append("ambulance_code_review")

    score = min(1.0, max(0.0, score))
    if score >= 0.75:
        risk_level = "high"
    elif score >= 0.4:
        risk_level = "medium"
    else:
        risk_level = "low"

    reason = (
        "Identified suspicious claim patterns: " + ", ".join(patterns)
        if patterns
        else "No suspicious fraud patterns detected."
    )

    return FraudScoreResponse(
        claim_id=request.claim_id,
        fraud_score=round(score, 3),
        risk_level=risk_level,
        patterns=patterns,
        reason=reason,
    )

@app.get("/health")
def health() -> JSONResponse:
    return JSONResponse(content={"status": "ok"})

mcp = FastApiMCP(app, name="MCP Policy Server", description="Healthcare Claims Processing MCP Policy Server")
mcp.mount_http()
