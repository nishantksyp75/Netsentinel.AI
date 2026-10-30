from app.detection.risk import risk_score, severity
def test_risk_boundaries():
    assert 0 <= risk_score(0,0) <= 1
    assert risk_score(1,1,1,1) == 1
    assert severity(.9) == "critical"
    assert severity(.7) == "high"
    assert severity(.4) == "medium"
    assert severity(.1) == "low"
