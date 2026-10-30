from __future__ import annotations
from uuid import uuid4
from app.database import Alert, Investigation, session
from app.rag import KnowledgeBase

def analyst_actions(alert: Alert) -> list[dict]:
    """Defensive, human-executed actions. The application never performs them."""
    actions = [
        {"priority": 1, "action": "Validate the alert scope", "reason": "Confirm the affected asset, time window, and model evidence before containment.", "status": "analyst action"},
        {"priority": 2, "action": "Preserve relevant evidence", "reason": "Retain flow records, alert identifiers, and timestamps for review and audit.", "status": "analyst action"},
    ]
    category = alert.predicted_class.lower()
    if "ddos" in category or "dos" in category:
        actions.append({"priority": 3, "action": "Review traffic-rate controls", "reason": "Ask the network/security team to assess approved rate-limiting or upstream protection options.", "status": "requires human approval"})
    elif "portscan" in category:
        actions.append({"priority": 3, "action": "Review exposed services", "reason": "Check whether the targeted service and scan pattern are expected; escalate unusual exposure for review.", "status": "requires human approval"})
    elif "brute" in category or "patator" in category:
        actions.append({"priority": 3, "action": "Review authentication activity", "reason": "Check account lockouts, failed-login patterns, and approved access records.", "status": "requires human approval"})
    else:
        actions.append({"priority": 3, "action": "Escalate for incident triage", "reason": "Review the supporting evidence with the designated incident-response owner.", "status": "requires human approval"})
    actions.append({"priority": 4, "action": "Record the analyst decision", "reason": "Approve or reject the recommendation and capture the rationale in the audit trail.", "status": "analyst action"})
    return actions

def similar_cases(alert_id: str, limit: int = 5) -> list[dict]:
    with session() as s:
        alert = s.get(Alert, alert_id)
        if not alert:
            raise KeyError(alert_id)
        candidates = s.query(Alert).filter(Alert.id != alert.id).order_by(Alert.created_at.desc()).limit(100).all()
        destination_port = alert.flow.get("Destination Port", alert.flow.get("destination_port"))
        ranked = []
        for item in candidates:
            candidate_port = item.flow.get("Destination Port", item.flow.get("destination_port"))
            signals = []
            score = 0.0
            if item.predicted_class == alert.predicted_class:
                score += 0.60; signals.append("same predicted class")
            if item.severity == alert.severity:
                score += 0.10; signals.append("same severity")
            score += 0.20 * max(0.0, 1.0 - abs(item.risk_score - alert.risk_score))
            if destination_port is not None and candidate_port == destination_port:
                score += 0.10; signals.append("same destination port")
            if score > 0.20:
                ranked.append((score, {"id": item.id, "created_at": item.created_at.isoformat(), "predicted_class": item.predicted_class,
                                       "severity": item.severity, "risk_score": item.risk_score, "status": item.status,
                                       "similarity_score": round(score, 3), "matching_signals": signals,
                                       "evidence_available": bool(item.evidence)}))
        return [case for _, case in sorted(ranked, key=lambda pair: pair[0], reverse=True)[:limit]]

def investigate(alert_id: str) -> Investigation:
    """Controlled, read-only investigation: it retrieves persisted evidence only."""
    with session() as s:
        alert=s.get(Alert, alert_id)
        if not alert: raise KeyError(alert_id)
        related=list(s.query(Alert).filter(Alert.id != alert.id, Alert.predicted_class == alert.predicted_class).order_by(Alert.created_at.desc()).limit(5))
        kb=KnowledgeBase(); sources=kb.search(f"{alert.predicted_class} network incident response {alert.severity}")
        trace=[{"tool":"get_alert","result":"retrieved structured alert"},{"tool":"find_related_alerts","result":f"{len(related)} related alerts"},{"tool":"get_model_evidence","result":"retrieved stored explanation evidence"},{"tool":"search_security_knowledge","result":f"{len(sources)} grounded sources"}]
        summary=(f"{alert.severity.title()}-priority {alert.predicted_class} alert. The supervised attack probability is {alert.attack_probability:.2%}, "
                 f"with anomaly evidence {alert.anomaly_score:.2%} and hybrid risk {alert.risk_score:.2%}. "
                 f"The investigation found {len(related)} related persisted alert(s).")
        recommendation="Human review required. Preserve relevant evidence and validate scope. Do not block traffic, change configurations, or contact external systems from this prototype."
        item=Investigation(id=f"INV-{uuid4().hex[:10]}",alert_id=alert.id,summary=summary,recommendation=recommendation,sources=sources,trace=trace); s.add(item); s.commit(); s.refresh(item); return item
