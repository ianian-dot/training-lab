from __future__ import annotations

from datetime import date
import re
from urllib.parse import parse_qs, quote, urlparse

import pandas as pd
from pandas.errors import EmptyDataError
import streamlit as st

from .config import (
    COLUMNS,
    COLUMN_ALIASES,
    DATA_DIR,
    EXERCISES,
    HEALTH_DAILY_PATH,
    LEGACY_FORM_PATH,
    PER_SIDE_BASE_LOAD_KG,
    SPORTS_PATH,
    WORKOUTS_PATH,
)

SPORTS_COLUMNS = [
    "date",
    "sport",
    "start_time",
    "duration_min",
    "calories",
    "intensity",
    "avg_heart_rate",
    "max_heart_rate",
    "notes",
]

HEALTH_DAILY_COLUMNS = [
    "date",
    "steps",
    "active_energy_kcal",
    "exercise_minutes",
    "stand_hours",
    "distance_km",
    "resting_heart_rate",
    "avg_heart_rate",
    "sleep_hours",
    "deep_sleep_hours",
    "rem_sleep_hours",
    "source",
    "received_at",
    "raw_payload_file",
]

def canonical_label(value: object) -> str:
    return str(value).strip().lower()


def row_value(row: pd.Series, lookup: dict[str, str], *labels: str) -> object:
    for label in labels:
        column = lookup.get(canonical_label(label))
        if column is not None:
            return row.get(column)
    return None


def first_filled(*values: object) -> object:
    for value in values:
        if is_filled(value):
            return value
    return None


def is_filled(value: object) -> bool:
    if pd.isna(value):
        return False
    return str(value).strip() != ""


def detect_exercise_name(value: object) -> str:
    if not is_filled(value):
        return ""

    raw = str(value).strip()
    if " / " in raw:
        possible_exercise = raw.split(" / ", 1)[1].strip()
        if possible_exercise:
            raw = possible_exercise

    normalized = canonical_label(raw).replace("-", " ")
    compact = " ".join(normalized.split())

    for exercise in EXERCISES:
        if canonical_label(exercise).replace("-", " ") == compact:
            return exercise

    if (
        ("incline" in compact or "inclined" in compact)
        and ("dumbbell" in compact or "db" in compact)
        and "press" in compact
    ):
        return "Incline dumbbell press"
    if (
        ("flat" in compact and ("dumbbell" in compact or "db" in compact) and "press" in compact)
        or "dumbbell bench press" in compact
    ):
        return "Flat dumbbell press"
    if ("pec" in compact or "pectoral" in compact or "pectorial" in compact) and (
        "fly" in compact or "deck" in compact
    ):
        return "Pectoral fly"
    if "reverse pec" in compact or "rear delt fly" in compact:
        return "Reverse pec deck"
    if "bicep hammer curl" in compact:
        return "Hammer curl"
    if ("calf" in compact or "calves" in compact) and "leg press" in compact:
        return "Leg press calf raise"
    if ("calf" in compact or "calves" in compact) and "press" in compact:
        return "Leg press calf raise"
    if "calve lag press" in compact or "calf leg press" in compact:
        return "Leg press calf raise"
    if "leg press" in compact:
        return "Leg press"
    if "hammer" in compact and ("curl" in compact or "bicep" in compact):
        return "Hammer curl"
    if "incline" in compact and ("bench" in compact or "press" in compact):
        return "Incline bench press"
    if "inclined" in compact and ("bench" in compact or "press" in compact):
        return "Incline bench press"
    if "stationary bike" in compact or "exercise bike" in compact:
        return "Stationary bike"
    if "cycling" in compact:
        return "Cycling"

    return raw


def start_time_from_parts(hour: object, minute: object) -> str | None:
    if not is_filled(hour):
        return None

    try:
        hour_number = int(float(str(hour).strip()))
    except ValueError:
        return None

    minute_number = 0
    if is_filled(minute):
        try:
            minute_number = int(float(str(minute).strip()))
        except ValueError:
            minute_number = 0

    if 0 <= hour_number <= 7:
        hour_number += 12
    if not 0 <= hour_number <= 23:
        return None

    minute_number = min(max(minute_number, 0), 59)
    return f"{hour_number:02d}:{minute_number:02d}"


def normalize_start_time_with_validation(value: object) -> tuple[object, str]:
    if not is_filled(value):
        return None, ""

    raw = str(value).strip()
    parsed = pd.to_datetime(raw, errors="coerce")
    if pd.isna(parsed):
        return value, "Could not parse start time"

    hour = int(parsed.hour)
    minute = int(parsed.minute)
    raw_lower = raw.lower()
    has_meridiem = "am" in raw_lower or "pm" in raw_lower
    has_pm = "pm" in raw_lower
    has_am = "am" in raw_lower
    compact_time = re.fullmatch(r"\s*(\d{1,2})(?::(\d{2}))?\s*", raw)

    validation = ""
    if 0 <= hour <= 7:
        hour += 12
        validation = "Inferred PM from unlikely early-morning gym time"
    elif has_am and 8 <= hour <= 11:
        validation = "Check AM time: kept as morning because 8-11am is plausible"
    elif compact_time and 1 <= hour <= 7:
        validation = "Inferred PM from 12-hour-looking time"
    elif compact_time and 8 <= hour <= 11:
        validation = "Ambiguous 8-11 time: kept as morning; use 20-23 for evening"
    elif has_pm:
        validation = "Explicit PM time"

    return f"{hour:02d}:{minute:02d}", validation


def normalize_date(value: object) -> object:
    if not is_filled(value):
        return pd.NaT
    return pd.to_datetime(value, errors="coerce")


def expand_multi_exercise_form(df: pd.DataFrame) -> pd.DataFrame:
    lookup = {canonical_label(column): column for column in df.columns}
    has_multi_exercise_columns = any(canonical_label(f"Exercise {index}") in lookup for index in range(1, 7))
    if not has_multi_exercise_columns:
        return df

    rows = []
    for _, form_row in df.iterrows():
        entry_type = row_value(form_row, lookup, "Entry type")
        workout_date = first_filled(
            row_value(form_row, lookup, "Date", "Workout date"),
            row_value(form_row, lookup, "Timestamp"),
        )
        start_time = first_filled(
            start_time_from_parts(
                row_value(form_row, lookup, "Start hour (24h)", "Start hour", "Workout hour"),
                row_value(form_row, lookup, "Start minute", "Workout minute"),
            ),
            row_value(form_row, lookup, "Start time"),
        )
        session_fields = {
            "date": workout_date,
            "start_time": start_time,
            "time_validation": None,
            "session_type": row_value(form_row, lookup, "Session", "Session type", "Entry type"),
            "duration_min": row_value(form_row, lookup, "Duration min", "Duration (min)"),
            "calories": row_value(form_row, lookup, "Calories"),
            "avg_heart_rate": row_value(form_row, lookup, "Avg heart rate", "Average heart rate"),
            "max_heart_rate": row_value(form_row, lookup, "Max heart rate"),
            "body_weight_kg": row_value(form_row, lookup, "Body weight kg", "Body weight (kg)"),
            "protein_taken": row_value(form_row, lookup, "Protein taken", "Took protein"),
            "protein_grams": row_value(form_row, lookup, "Protein grams"),
            "energy": row_value(form_row, lookup, "Energy"),
            "motivation": row_value(form_row, lookup, "Motivation"),
            "session_quality": row_value(form_row, lookup, "Session quality", "Gym session quality"),
            "productivity": row_value(form_row, lookup, "Productivity"),
            "sleep_hours": row_value(form_row, lookup, "Sleep hours", "Sleep (hours)"),
            "feeling": row_value(form_row, lookup, "Feeling", "How I am feeling", "How im feeling"),
        }

        session_notes = row_value(form_row, lookup, "Session notes", "Notes")
        row_count_before = len(rows)
        for index in range(1, 7):
            exercise = row_value(form_row, lookup, f"Exercise {index}")
            other_exercise = row_value(form_row, lookup, f"Other exercise {index}")
            if is_filled(other_exercise):
                exercise = other_exercise

            if not is_filled(exercise):
                continue

            exercise_name = detect_exercise_name(exercise)
            if exercise_name.lower() == "other":
                continue

            muscle_group = row_value(form_row, lookup, f"Muscle group {index}")
            if not is_filled(muscle_group):
                muscle_group = EXERCISES.get(exercise_name, "Full body")

            exercise_notes = row_value(form_row, lookup, f"Exercise notes {index}", f"Notes {index}")
            notes = " | ".join(
                str(note).strip()
                for note in [exercise_notes, session_notes]
                if is_filled(note)
            )

            rows.append(
                {
                    **session_fields,
                    "exercise": exercise_name,
                    "muscle_group": muscle_group,
                    "sets": row_value(form_row, lookup, f"Sets {index}"),
                    "reps": row_value(form_row, lookup, f"Reps {index}"),
                    "weight_kg": row_value(form_row, lookup, f"Weight kg {index}", f"Weight (kg) {index}"),
                    "weight_basis": row_value(form_row, lookup, f"Weight basis {index}"),
                    "rpe": row_value(form_row, lookup, f"RPE {index}"),
                    "notes": notes,
                }
            )

        has_session_update = any(
            is_filled(session_fields[field])
            for field in [
                "duration_min",
                "calories",
                "avg_heart_rate",
                "max_heart_rate",
                "body_weight_kg",
                "protein_taken",
                "protein_grams",
                "energy",
                "motivation",
                "session_quality",
                "productivity",
                "sleep_hours",
                "feeling",
            ]
        )
        no_exercises_added = len(rows) == row_count_before
        if no_exercises_added and has_session_update:
            notes = " | ".join(
                str(note).strip()
                for note in [entry_type, session_notes]
                if is_filled(note)
            )
            rows.append(
                {
                    **session_fields,
                    "session_type": (
                        session_fields["session_type"]
                        if is_filled(session_fields["session_type"])
                        else "Session update"
                    ),
                    "exercise": "Session update",
                    "muscle_group": "Recovery",
                    "sets": None,
                    "reps": None,
                    "weight_kg": None,
                    "weight_basis": None,
                    "rpe": None,
                    "notes": notes,
                }
            )

    return pd.DataFrame(rows, columns=COLUMNS)


def ensure_data_file() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    if WORKOUTS_PATH.exists():
        return

    pd.DataFrame(
        [
            {
                "date": date.today().isoformat(),
                "start_time": "18:30",
                "session_type": "Upper",
                "exercise": "Bench press",
                "muscle_group": "Chest",
                "sets": 4,
                "reps": 8,
                "weight_kg": 40.0,
                "weight_basis": "total",
                "rpe": 7,
                "duration_min": 60,
                "calories": 0,
                "avg_heart_rate": None,
                "max_heart_rate": None,
                "body_weight_kg": None,
                "protein_taken": None,
                "protein_grams": None,
                "energy": 7,
                "motivation": None,
                "session_quality": None,
                "productivity": None,
                "sleep_hours": 7.0,
                "feeling": None,
                "notes": "Sample row. Replace this with your own workout.",
            }
        ],
        columns=COLUMNS,
    ).to_csv(WORKOUTS_PATH, index=False)


def estimate_one_rep_max(row: pd.Series) -> float:
    reps = row.get("reps")
    weight = row.get("load_kg", row.get("weight_kg"))
    if pd.isna(reps) or pd.isna(weight) or reps <= 0 or weight <= 0:
        return 0.0
    return round(float(weight) * (1 + float(reps) / 30), 1)


def calculate_load_kg(row: pd.Series) -> float:
    weight = row.get("weight_kg")
    if pd.isna(weight):
        return 0.0

    weight = float(weight)
    basis = str(row.get("weight_basis", "")).strip().lower()
    exercise = str(row.get("exercise", "")).strip()

    if basis == "per side" and exercise in PER_SIDE_BASE_LOAD_KG:
        return PER_SIDE_BASE_LOAD_KG[exercise] + weight * 2
    if basis in {"per hand", "per side", "each arm"}:
        return weight * 2
    return weight


def normalize_workouts(df: pd.DataFrame) -> pd.DataFrame:
    df = expand_multi_exercise_form(df.copy())
    df.columns = [COLUMN_ALIASES.get(str(column).strip().lower(), str(column).strip()) for column in df.columns]

    if "other_exercise" in df.columns:
        other = df["other_exercise"].fillna("").astype(str).str.strip()
        exercise = df.get("exercise", pd.Series("", index=df.index)).fillna("").astype(str).str.strip()
        df["exercise"] = exercise.where(other == "", other)

    for column in COLUMNS:
        if column not in df.columns:
            df[column] = None

    df = df[COLUMNS]
    df["exercise"] = df["exercise"].apply(detect_exercise_name)
    normalized_times = df["start_time"].apply(normalize_start_time_with_validation)
    df["start_time"] = normalized_times.apply(lambda value: value[0])
    df["time_validation"] = normalized_times.apply(lambda value: value[1])
    missing_group = df["muscle_group"].isna() | (df["muscle_group"].fillna("").astype(str).str.strip() == "")
    df.loc[missing_group, "muscle_group"] = df.loc[missing_group, "exercise"].map(EXERCISES).fillna("Full body")
    df["date"] = df["date"].apply(normalize_date)
    for column in [
        "sets",
        "reps",
        "weight_kg",
        "rpe",
        "duration_min",
        "calories",
        "avg_heart_rate",
        "max_heart_rate",
        "body_weight_kg",
        "protein_grams",
        "energy",
        "motivation",
        "session_quality",
        "productivity",
        "sleep_hours",
    ]:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df["load_kg"] = df.apply(calculate_load_kg, axis=1)
    df["volume_kg"] = df["sets"].fillna(0) * df["reps"].fillna(0) * df["load_kg"].fillna(0)
    df["estimated_1rm_kg"] = df.apply(estimate_one_rep_max, axis=1)
    return df


@st.cache_data(ttl=60)
def read_google_sheet_csv(sheet_url: str) -> pd.DataFrame:
    try:
        return pd.read_csv(to_google_sheet_csv_url(sheet_url))
    except EmptyDataError:
        return pd.DataFrame()


def to_google_sheet_csv_url(sheet_url: str) -> str:
    if "export?format=csv" in sheet_url:
        return sheet_url

    parsed = urlparse(sheet_url)
    path_parts = [part for part in parsed.path.split("/") if part]
    try:
        spreadsheet_id = path_parts[path_parts.index("d") + 1]
    except (ValueError, IndexError):
        return sheet_url

    query = parse_qs(parsed.query)
    fragment_query = parse_qs(parsed.fragment)
    gid = query.get("gid", fragment_query.get("gid", [None]))[0]
    if gid is None:
        sheet_name = quote("Form Responses 1")
        return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"

    return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid={gid}"


def load_workouts(csv_url: str | None = None) -> pd.DataFrame:
    ensure_data_file()
    frames = [normalize_workouts(pd.read_csv(WORKOUTS_PATH))]

    if LEGACY_FORM_PATH.exists():
        try:
            frames.append(normalize_workouts(pd.read_csv(LEGACY_FORM_PATH)))
        except Exception as exc:
            st.sidebar.error(f"Could not load legacy Google Form CSV: {exc}")

    if csv_url:
        try:
            frames.append(normalize_workouts(read_google_sheet_csv(csv_url)))
        except Exception as exc:
            st.sidebar.error(f"Could not load Google Sheet CSV: {exc}")
            st.sidebar.info("Make sure the sheet is shared as 'Anyone with the link can view' or published to the web.")

    combined = pd.concat(frames, ignore_index=True)
    dedupe_columns = ["date", "exercise", "sets", "reps", "weight_kg", "weight_basis", "notes"]
    return combined.drop_duplicates(subset=dedupe_columns, keep="last").reset_index(drop=True)


def append_workout(row: dict) -> None:
    ensure_data_file()
    df = pd.read_csv(WORKOUTS_PATH)
    for column in COLUMNS:
        if column not in df.columns:
            df[column] = None
    df = df[COLUMNS]
    df = pd.concat([df, pd.DataFrame([row], columns=COLUMNS)], ignore_index=True)
    df.to_csv(WORKOUTS_PATH, index=False)


def ensure_sports_file() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    if SPORTS_PATH.exists():
        return

    pd.DataFrame(
        [
            {
                "date": "2026-05-25",
                "sport": "Pickleball",
                "start_time": None,
                "duration_min": None,
                "calories": 450,
                "intensity": None,
                "avg_heart_rate": None,
                "max_heart_rate": None,
                "notes": "Backfilled from memory. Calories estimated using 400-500 kcal active range.",
            },
            {
                "date": "2026-05-26",
                "sport": "Pickleball",
                "start_time": None,
                "duration_min": None,
                "calories": 450,
                "intensity": None,
                "avg_heart_rate": None,
                "max_heart_rate": None,
                "notes": "Backfilled from memory. Calories estimated using 400-500 kcal active range.",
            },
            {
                "date": "2026-05-27",
                "sport": "Pickleball",
                "start_time": None,
                "duration_min": None,
                "calories": 450,
                "intensity": None,
                "avg_heart_rate": None,
                "max_heart_rate": None,
                "notes": "Backfilled from memory. Calories estimated using 400-500 kcal active range.",
            },
            {
                "date": "2026-06-01",
                "sport": "Pickleball",
                "start_time": None,
                "duration_min": None,
                "calories": 450,
                "intensity": None,
                "avg_heart_rate": None,
                "max_heart_rate": None,
                "notes": "Backfilled from memory. First of two pickleball sessions that day. Calories estimated.",
            },
            {
                "date": "2026-06-01",
                "sport": "Pickleball",
                "start_time": None,
                "duration_min": None,
                "calories": 450,
                "intensity": None,
                "avg_heart_rate": None,
                "max_heart_rate": None,
                "notes": "Backfilled from memory. Second of two pickleball sessions that day. Calories estimated.",
            },
            {
                "date": "2026-06-02",
                "sport": "Pickleball",
                "start_time": None,
                "duration_min": None,
                "calories": 450,
                "intensity": None,
                "avg_heart_rate": None,
                "max_heart_rate": None,
                "notes": "Backfilled from memory. Calories estimated using 400-500 kcal active range.",
            },
        ],
        columns=SPORTS_COLUMNS,
    ).to_csv(SPORTS_PATH, index=False)


def load_sports() -> pd.DataFrame:
    ensure_sports_file()
    sports = pd.read_csv(SPORTS_PATH)
    for column in SPORTS_COLUMNS:
        if column not in sports.columns:
            sports[column] = None
    sports = sports[SPORTS_COLUMNS]
    sports["date"] = sports["date"].apply(normalize_date)
    sports["start_time"] = sports["start_time"].apply(lambda value: normalize_start_time_with_validation(value)[0])
    for column in ["duration_min", "calories", "intensity", "avg_heart_rate", "max_heart_rate"]:
        sports[column] = pd.to_numeric(sports[column], errors="coerce")
    return sports.sort_values("date").reset_index(drop=True)


def normalize_health_daily(health: pd.DataFrame) -> pd.DataFrame:
    for column in HEALTH_DAILY_COLUMNS:
        if column not in health.columns:
            health[column] = None
    health = health[HEALTH_DAILY_COLUMNS]
    health["date"] = health["date"].apply(normalize_date)
    for column in [
        "steps",
        "active_energy_kcal",
        "exercise_minutes",
        "stand_hours",
        "distance_km",
        "resting_heart_rate",
        "avg_heart_rate",
        "sleep_hours",
        "deep_sleep_hours",
        "rem_sleep_hours",
    ]:
        health[column] = pd.to_numeric(health[column], errors="coerce")
    return health.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)


def load_health_daily(sheet_url: str | None = None) -> pd.DataFrame:
    frames = []

    if HEALTH_DAILY_PATH.exists():
        frames.append(normalize_health_daily(pd.read_csv(HEALTH_DAILY_PATH)))

    if sheet_url:
        try:
            frames.append(normalize_health_daily(read_google_sheet_csv(sheet_url)))
        except Exception as exc:
            st.sidebar.error(f"Could not load Apple Health Google Sheet: {exc}")
            st.sidebar.info("Make sure the health sheet is shared as 'Anyone with the link can view' or published to the web.")

    if not frames:
        return pd.DataFrame(columns=HEALTH_DAILY_COLUMNS)

    combined = pd.concat(frames, ignore_index=True)
    return combined.drop_duplicates(subset=["date"], keep="last").sort_values("date").reset_index(drop=True)
