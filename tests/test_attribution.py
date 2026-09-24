"""Real tests: hand-checked attribution math on a fixed sample."""
import io
import pandas as pd
from fastapi.testclient import TestClient
from main import app, credit_journey, attribute, parse_touchpoints

client = TestClient(app)

CSV = """journey_id,channel,timestamp,converted,conversion_value
J1,email,2024-01-01T10:00:00,1,100
J1,social,2024-01-03T10:00:00,1,100
J1,search,2024-01-05T10:00:00,1,100
J2,social,2024-02-01T09:00:00,1,60
J2,email,2024-02-08T09:00:00,1,60
J3,email,2024-03-01T10:00:00,0,0
"""


def df():
    return pd.read_csv(io.StringIO(CSV))


def test_hand_checked_totals():
    res = attribute(parse_touchpoints(_fake_upload()), half_life_days=7.0)
    m = res["models"]
    assert res["converted_journeys"] == 2  # J3 not converted
    assert res["total_conversion_value"] == 160.0
    # first touch: J1->email 100, J2->social 60
    assert m["first_touch"] == {"email": 100.0, "social": 60.0}
    # last touch: J1->search 100, J2->email 60
    assert m["last_touch"] == {"email": 60.0, "search": 100.0}
    # linear: J1 33.333 each; J2 30 each
    assert abs(m["linear"]["email"] - (100 / 3 + 30)) < 1e-3
    assert abs(m["linear"]["social"] - (100 / 3 + 30)) < 1e-3
    assert abs(m["linear"]["search"] - 100 / 3) < 1e-3
    # position based: J1 email 40, search 40, social 20; J2 social 30, email 30
    assert m["position_based"] == {"email": 70.0, "search": 40.0, "social": 50.0}
    # every model sums to total conversion value
    for model, credits in m.items():
        assert abs(sum(credits.values()) - 160.0) < 1e-3, model


def test_time_decay_ordering_and_sum():
    from datetime import datetime
    channels = ["email", "social", "search"]
    times = [datetime(2024, 1, 1), datetime(2024, 1, 8), datetime(2024, 1, 15)]
    per = credit_journey(channels, times, 100.0, 7.0)["time_decay"]
    # later touches earn strictly more
    assert per["search"] > per["social"] > per["email"]
    assert abs(sum(per.values()) - 100.0) < 1e-9
    # half-life check: touches 7 days apart -> weight ratio exactly 2
    times2 = [datetime(2024, 1, 1), datetime(2024, 1, 8)]
    per2 = credit_journey(["a", "b"], times2, 90.0, 7.0)["time_decay"]
    assert abs(per2["b"] / per2["a"] - 2.0) < 1e-9
    assert abs(per2["b"] - 60.0) < 1e-9 and abs(per2["a"] - 30.0) < 1e-9


def test_single_touch_journey():
    from datetime import datetime
    per = credit_journey(["email"], [datetime(2024, 1, 1)], 50.0, 7.0)
    for model in per:
        assert per[model] == {"email": 50.0}


def _fake_upload():
    class F:
        filename = "t.csv"
        file = io.BytesIO(CSV.encode())
    return F()


def test_endpoint_csv():
    r = client.post("/attribute", files={"file": ("t.csv", CSV.encode(), "text/csv")})
    assert r.status_code == 200
    body = r.json()
    assert body["models"]["first_touch"] == {"email": 100.0, "social": 60.0}
    assert body["converted_journeys"] == 2


def test_endpoint_rejects_bad_input():
    r = client.post("/attribute", files={"file": ("t.csv", b"a,b\n1,2", "text/csv")})
    assert r.status_code == 400
