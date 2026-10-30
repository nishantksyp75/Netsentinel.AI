from __future__ import annotations
from contextlib import asynccontextmanager
from collections import defaultdict, deque
import time
from uuid import uuid4
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from app.agents import analyst_actions, investigate, similar_cases
from app.database import Alert, Decision, Investigation, init_db, recent_alerts, session
from app.detection.risk import risk_score, severity
from app.config import API_KEY, MODEL_DIR, RATE_LIMIT_PER_MINUTE
from app.detection.service import Detector
from app.explainability import feature_evidence

@asynccontextmanager
async def lifespan(app: FastAPI): init_db(); yield
app=FastAPI(title="NetSentinel AI", version="0.1.0", lifespan=lifespan)
request_history: dict[str, deque[float]] = defaultdict(deque)

@app.middleware("http")
async def protect_api(request: Request, call_next):
    if request.url.path not in {"/health", "/docs", "/openapi.json", "/redoc"}:
        if API_KEY and request.headers.get("X-API-Key") != API_KEY:
            return JSONResponse(status_code=401, content={"detail":"Missing or invalid API key"})
        if RATE_LIMIT_PER_MINUTE > 0:
            client = request.client.host if request.client else "unknown"
            now = time.monotonic(); history = request_history[client]
            while history and now - history[0] >= 60:
                history.popleft()
            if len(history) >= RATE_LIMIT_PER_MINUTE:
                return JSONResponse(status_code=429, content={"detail":"Rate limit exceeded"})
            history.append(now)
    return await call_next(request)
class AlertIn(BaseModel):
    predicted_class: str; attack_probability: float=Field(ge=0,le=1); anomaly_score: float=Field(ge=0,le=1); flow: dict={}; evidence: dict={}
class DecisionIn(BaseModel): decision: str=Field(pattern="^(approved|rejected)$"); comment: str=""
class FlowIn(BaseModel): flow: dict
def show(a: Alert): return {"id":a.id,"created_at":a.created_at,"status":a.status,"predicted_class":a.predicted_class,"attack_probability":a.attack_probability,"anomaly_score":a.anomaly_score,"risk_score":a.risk_score,"severity":a.severity,"flow":a.flow,"evidence":a.evidence}
@app.get("/health")
def health(): return {"status":"ok"}
@app.get("/alerts")
def alerts(limit:int=100): return [show(a) for a in recent_alerts(min(limit,200))]
@app.post("/alerts", status_code=201)
def create_alert(item: AlertIn):
    score=risk_score(item.attack_probability,item.anomaly_score,float(item.evidence.get("score",0)),0)
    alert=Alert(id=f"ALT-{uuid4().hex[:10]}",predicted_class=item.predicted_class,attack_probability=item.attack_probability,anomaly_score=item.anomaly_score,risk_score=score,severity=severity(score),flow=item.flow,evidence=item.evidence)
    with session() as s: s.add(alert); s.commit(); s.refresh(alert); return show(alert)
@app.post("/score", status_code=201)
def score_flow(item: FlowIn):
    model_path=MODEL_DIR / "detectors.joblib"
    if not model_path.exists(): raise HTTPException(409,"No trained model. Run scripts/train.py with CIC-IDS2017 first.")
    detector=Detector(model_path); result=detector.predict(item.flow); evidence=feature_evidence(detector,item.flow)
    alert=Alert(id=f"ALT-{uuid4().hex[:10]}",flow=item.flow,evidence={"features":evidence},**result)
    with session() as s: s.add(alert); s.commit(); s.refresh(alert); return show(alert)
@app.get("/alerts/{alert_id}")
def alert(alert_id:str):
    with session() as s:
        a=s.get(Alert,alert_id)
        if not a: raise HTTPException(404,"Alert not found")
        return show(a)
@app.get("/alerts/{alert_id}/explanation")
def explanation(alert_id:str):
    with session() as s:
        a=s.get(Alert,alert_id)
        if not a: raise HTTPException(404,"Alert not found")
        return {"alert_id":a.id,"evidence":a.evidence}
@app.get("/alerts/{alert_id}/similar-cases")
def get_similar_cases(alert_id: str, limit: int = 5):
    try:
        return {"alert_id": alert_id, "cases": similar_cases(alert_id, min(max(limit, 1), 20))}
    except KeyError:
        raise HTTPException(404, "Alert not found")
@app.post("/investigate/{alert_id}")
def start_investigation(alert_id:str):
    try: i=investigate(alert_id)
    except KeyError: raise HTTPException(404,"Alert not found")
    with session() as s:
        alert=s.get(Alert, alert_id)
        return {"id":i.id,"alert_id":i.alert_id,"summary":i.summary,"recommendation":i.recommendation,"sources":i.sources,"trace":i.trace,"analyst_actions":analyst_actions(alert)}
@app.get("/investigations/{investigation_id}")
def get_investigation(investigation_id:str):
    with session() as s:
        i=s.get(Investigation,investigation_id)
        if not i: raise HTTPException(404,"Investigation not found")
        return {"id":i.id,"alert_id":i.alert_id,"created_at":i.created_at,"summary":i.summary,"recommendation":i.recommendation,"sources":i.sources,"trace":i.trace}
@app.get("/investigations/{investigation_id}/timeline")
def investigation_timeline(investigation_id: str):
    with session() as s:
        inv=s.get(Investigation,investigation_id)
        if not inv: raise HTTPException(404,"Investigation not found")
        events=[{"timestamp":inv.created_at.isoformat(),"event":"investigation_created","detail":"Controlled evidence retrieval completed"}]
        decisions=s.scalars(select(Decision).where(Decision.investigation_id == inv.id).order_by(Decision.created_at)).all()
        events.extend({"timestamp":item.created_at.isoformat(),"event":f"analyst_{item.decision}","detail":item.comment or "No rationale supplied"} for item in decisions)
        return {"investigation_id":inv.id,"events":events}
@app.post("/incidents/{investigation_id}/decision")
def decide(investigation_id:str,item:DecisionIn):
    with session() as s:
        inv=s.get(Investigation,investigation_id)
        if not inv: raise HTTPException(404,"Investigation not found")
        decision=Decision(id=f"DEC-{uuid4().hex[:10]}",investigation_id=inv.id,decision=item.decision,comment=item.comment); s.add(decision); inv.alert.status=item.decision; s.commit(); s.refresh(decision); return {"id":decision.id,"decision":decision.decision,"comment":decision.comment,"created_at":decision.created_at}
@app.get("/metrics")
def metrics():
    path=MODEL_DIR / "metrics.json"
    if not path.exists(): raise HTTPException(404,"No experiment metrics. Train a model first.")
    import json
    return json.loads(path.read_text(encoding="utf-8"))

from sqlalchemy import select
