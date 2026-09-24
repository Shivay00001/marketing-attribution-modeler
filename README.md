# Marketing Attribution Modeler

**What it does:** Upload touchpoint data (CSV or JSON) and get conversion
credit split across channels under five standard, fully documented models:
first-touch, last-touch, linear, time-decay (configurable half-life), and
position-based (40/20/40). Only converted journeys distribute credit, and each
journey's credit always sums to its conversion value.

**What it does NOT do:** No ML, no "AI attribution" — deterministic math only.

## Run

```bash
pip install -r requirements.txt
uvicorn main:app --port 8000
```

## API

- `GET /models` — model definitions
- `POST /attribute` — multipart CSV/JSON upload
  (`journey_id,channel,timestamp,converted,conversion_value`), optional
  `?half_life_days=7`

```bash
curl -F "file=@sample_touchpoints.csv" "http://localhost:8000/attribute?half_life_days=7"
```

## Tests

```bash
pytest -q   # hand-checked model math incl. half-life ratio identity
```
