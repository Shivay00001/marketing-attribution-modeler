"""Real multi-touch marketing attribution math.

Upload touchpoint data (CSV or JSON) and get conversion credit split across
channels under five standard models. Only *converted* journeys distribute
credit; credit per journey always sums to that journey's conversion value.

Models (documented, deterministic):
  - first_touch: 100% to the first touchpoint's channel.
  - last_touch: 100% to the last touchpoint's channel.
  - linear: conversion value split evenly across all touchpoints.
  - time_decay: weight w_i = 0.5 ** ((t_last - t_i) / half_life_days);
    later touches get exponentially more credit; normalized to sum to value.
  - position_based: 40% first, 40% last, 20% split evenly among middle touches
    (2-touch journeys: 50/50; 1-touch: 100%).
"""

import io
import math
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
import pandas as pd

app = FastAPI(title="Marketing Attribution Modeler")

REQUIRED_COLS = ["journey_id", "channel", "timestamp", "converted", "conversion_value"]


def parse_touchpoints(file: UploadFile) -> pd.DataFrame:
    name = (file.filename or "").lower()
    try:
        raw = file.file.read()
        if name.endswith(".json"):
            df = pd.read_json(io.BytesIO(raw))
        else:
            df = pd.read_csv(io.BytesIO(raw))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(400, f"Could not parse upload: {exc}")
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise HTTPException(400, f"Missing columns: {missing}")
    if df.empty:
        raise HTTPException(400, "No touchpoint rows")
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    if df["timestamp"].isna().any():
        raise HTTPException(400, "Unparseable timestamp values")
    df["converted"] = df["converted"].astype(int)
    df["conversion_value"] = df["conversion_value"].astype(float)
    return df.sort_values(["journey_id", "timestamp"]).reset_index(drop=True)


def credit_journey(channels: list[str], times: list[datetime], value: float,
                   half_life_days: float) -> dict[str, dict[str, float]]:
    """Return {model: {channel: credit}} for one converted journey."""
    n = len(channels)
    out: dict[str, dict[str, float]] = {}

    out["first_touch"] = {channels[0]: value}

    out["last_touch"] = {channels[-1]: value}

    linear = {}
    for c in channels:
        linear[c] = linear.get(c, 0.0) + value / n
    out["linear"] = linear

    t_last = times[-1]
    weights = [0.5 ** ((t_last - t).total_seconds() / 86400.0 / half_life_days) for t in times]
    wsum = sum(weights)
    decay = {}
    for c, w in zip(channels, weights):
        decay[c] = decay.get(c, 0.0) + value * w / wsum
    out["time_decay"] = decay

    if n == 1:
        pos = {channels[0]: value}
    elif n == 2:
        pos = {channels[0]: value * 0.5, channels[1]: value * 0.5}
    else:
        pos = {channels[0]: value * 0.4, channels[-1]: value * 0.4}
        for c in channels[1:-1]:
            pos[c] = pos.get(c, 0.0) + value * 0.2 / (n - 2)
    out["position_based"] = pos
    return out


def attribute(df: pd.DataFrame, half_life_days: float = 7.0) -> dict:
    models = ["first_touch", "last_touch", "linear", "time_decay", "position_based"]
    totals = {m: {} for m in models}
    journeys = []
    for jid, grp in df.groupby("journey_id", sort=False):
        channels = grp["channel"].tolist()
        times = grp["timestamp"].tolist()
        converted = bool(grp["converted"].iloc[0])
        value = float(grp["conversion_value"].iloc[0])
        if not converted or value <= 0:
            continue
        per_model = credit_journey(channels, times, value, half_life_days)
        journeys.append({"journey_id": str(jid), "channels": channels,
                         "conversion_value": value,
                         "credit": {m: dict(v) for m, v in per_model.items()}})
        for m in models:
            for c, credit in per_model[m].items():
                totals[m][c] = totals[m].get(c, 0.0) + credit
    total_value = sum(j["conversion_value"] for j in journeys)
    for m in models:
        s = sum(totals[m].values())
        assert abs(s - total_value) < 1e-6 or total_value == 0, f"{m} credit does not sum to conversions"
    return {
        "converted_journeys": len(journeys),
        "total_conversion_value": total_value,
        "models": {m: {c: round(v, 4) for c, v in sorted(totals[m].items())} for m in models},
        "journeys": journeys,
    }


class Options(BaseModel):
    half_life_days: float = 7.0


@app.get("/health")
def health():
    return {"status": "ok", "models": ["first_touch", "last_touch", "linear", "time_decay", "position_based"]}


@app.get("/models")
def model_docs():
    return {"models": {
        "first_touch": "100% credit to first touchpoint",
        "last_touch": "100% credit to last touchpoint",
        "linear": "credit split evenly across all touchpoints",
        "time_decay": "weight = 0.5^((t_last - t_i)/half_life_days); later touches earn more",
        "position_based": "40% first, 40% last, 20% split among middle touches",
    }}


@app.post("/attribute")
def attribute_csv(file: UploadFile = File(...), half_life_days: float = 7.0):
    df = parse_touchpoints(file)
    return attribute(df, half_life_days)
