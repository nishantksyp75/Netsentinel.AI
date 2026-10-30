from fastapi.testclient import TestClient
from app.api.main import app
def test_health():
    with TestClient(app) as c: assert c.get("/health").json()["status"] == "ok"
def test_alert_and_investigation():
    with TestClient(app) as c:
        a=c.post("/alerts",json={"predicted_class":"DDoS","attack_probability":.9,"anomaly_score":.8,"flow":{"destination_port":80}}).json()
        assert a["risk_score"] > .5
        inv=c.post(f"/investigate/{a['id']}").json()
        assert inv["alert_id"] == a["id"]
        assert inv["analyst_actions"]
        assert c.get(f"/alerts/{a['id']}/explanation").status_code == 200
        assert c.get(f"/alerts/{a['id']}/similar-cases").status_code == 200
        assert c.get(f"/investigations/{inv['id']}").status_code == 200
        assert c.post(f"/incidents/{inv['id']}/decision",json={"decision":"approved","comment":"reviewed"}).status_code == 200
        timeline=c.get(f"/investigations/{inv['id']}/timeline").json()
        assert len(timeline["events"]) >= 2
        assert timeline["events"][-1]["event"] == "analyst_approved"
