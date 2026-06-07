from __future__ import annotations

import csv
from datetime import datetime
import json
from typing import Any

from fastapi import FastAPI, Request

from training_app.config import DATA_DIR, HEALTH_DAILY_PATH, HEALTH_RAW_DIR
from training_app.data import HEALTH_DAILY_COLUMNS

app = FastAPI(title="Training Lab Health Receiver")


FIELD_ALIASES = {
    "date": ["date", "day", "workout_date"],
    "steps": ["steps", "step_count", "stepCount"],
    "active_energy_kcal": ["active_energy_kcal", "activeEnergy", "active_energy", "active_calories", "calories"],
    "exercise_minutes": ["exercise_minutes", "exerciseTime", "apple_exercise_minutes"],
    "stand_hours": ["stand_hours", "standHours"],
    "distance_km": ["distance_km", "walking_running_distance_km", "distance"],
    "resting_heart_rate": ["resting_heart_rate", "restingHeartRate", "resting_hr"],
    "avg_heart_rate": ["avg_heart_rate", "average_heart_rate", "averageHeartRate", "avg_hr"],
    "sleep_hours": ["sleep_hours", "sleep", "sleepAnalysis"],
    "deep_sleep_hours": ["deep_sleep_hours", "deepSleep", "deep_sleep"],
    "rem_sleep_hours": ["rem_sleep_hours", "remSleep", "rem_sleep"],
}


def first_value(payload: dict[str, Any], field: str) -> Any:
    metrics = payload.get("metrics")
    sources = [payload]
    if isinstance(metrics, dict):
        sources.insert(0, metrics)

    for source in sources:
        for alias in FIELD_ALIASES[field]:
            if alias in source:
                return source[alias]
    return None


def number_or_blank(value: Any) -> Any:
    if value is None or value == "":
        return ""
    if isinstance(value, list):
        values = [number_or_blank(item) for item in value]
        numeric = [float(item) for item in values if item != ""]
        return sum(numeric) if numeric else ""
    if isinstance(value, dict):
        for key in ["value", "quantity", "sum", "total", "average"]:
            if key in value:
                return number_or_blank(value[key])
        return ""
    try:
        return float(str(value).replace(",", ""))
    except ValueError:
        return value


def payload_date(payload: dict[str, Any]) -> str:
    value = first_value(payload, "date")
    if value:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed.date().isoformat()
    return datetime.now().date().isoformat()


def raw_payload_path(received_at: str) -> str:
    HEALTH_RAW_DIR.mkdir(parents=True, exist_ok=True)
    file_name = received_at.replace(":", "").replace(".", "-") + ".json"
    return str(HEALTH_RAW_DIR / file_name)


def read_existing_rows() -> list[dict[str, Any]]:
    if not HEALTH_DAILY_PATH.exists():
        return []
    with HEALTH_DAILY_PATH.open(newline="") as file:
        return list(csv.DictReader(file))


def write_rows(rows: list[dict[str, Any]]) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    with HEALTH_DAILY_PATH.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=HEALTH_DAILY_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def upsert_daily_row(row: dict[str, Any]) -> None:
    rows = read_existing_rows()
    rows = [existing for existing in rows if existing.get("date") != row["date"]]
    rows.append(row)
    rows.sort(key=lambda item: item.get("date", ""))
    write_rows(rows)


def normalize_payload(payload: dict[str, Any], received_at: str, raw_file: str) -> dict[str, Any]:
    row = {column: "" for column in HEALTH_DAILY_COLUMNS}
    row["date"] = payload_date(payload)
    for field in FIELD_ALIASES:
        if field == "date":
            continue
        row[field] = number_or_blank(first_value(payload, field))
    row["source"] = str(payload.get("source", "iphone_shortcuts"))
    row["received_at"] = received_at
    row["raw_payload_file"] = raw_file
    return row


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/health-data")
async def receive_health_data(request: Request) -> dict[str, Any]:
    payload = await request.json()
    if not isinstance(payload, dict):
        return {"status": "error", "message": "Expected a JSON dictionary."}

    received_at = datetime.now().isoformat(timespec="seconds")
    raw_file = raw_payload_path(received_at)
    with open(raw_file, "w") as file:
        json.dump(payload, file, indent=2)

    row = normalize_payload(payload, received_at, raw_file)
    upsert_daily_row(row)
    return {"status": "success", "saved_date": row["date"], "path": str(HEALTH_DAILY_PATH)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
