"""
FastAPI REST API Server for Padua Vte Prediction Score.
"""
import hmac
import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from .base import AuditLogger, PHIGuard, SecurityException
from .models import SystemTaskPayload, ConsensusDossier
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Padua Vte Prediction Score API",
    description="Optional local-only experimental task-audit demo; not a Padua risk API.",
    version="1.0.0",
)


@app.middleware("http")
async def require_api_key(request: Request, call_next):
    if request.url.path == "/health":
        return await call_next(request)
    expected = os.getenv("AUDIT_API_KEY")
    if not expected:
        return JSONResponse(status_code=503, content={"detail": "AUDIT_API_KEY not configured"})
    supplied = request.headers.get("x-api-key", "")
    if not hmac.compare_digest(supplied, expected):
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
    return await call_next(request)


class ChatRequest(BaseModel):
    query: str


@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "padua-vte-prediction-score", "api_key_configured": bool(os.getenv("AUDIT_API_KEY")), "version": "1.0.0"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": "NOMINAL_OPTIMAL"
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    try:
        dossier = supervisor.process_task(payload)
    except SecurityException:
        raise HTTPException(status_code=400, detail="Input contains a restricted identifier")
    return dossier.to_dict()


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans}
    except SecurityException:
        raise HTTPException(status_code=400, detail="Input contains a restricted identifier")


@app.get("/api/audit/logs")
def api_audit_logs():
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}
