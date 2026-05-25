from __future__ import annotations

from datetime import date, datetime, time
from html import escape
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components


APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "data"
WORKOUTS_PATH = DATA_DIR / "workouts.csv"
FORM_SCRIPT_PATH = APP_DIR / "google_form_creator.gs"
DEFAULT_GOOGLE_SHEET_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1WBjw_OY7rI-RWbt9BzsxeHJ0xtOTXZqyP1gRqCjQ-4w/edit?gid=998599074#gid=998599074"
)

EXERCISES = {
    "Bench press": "Chest",
    "Seated lateral raise machine": "Shoulders",
    "Barbell bicep curl": "Biceps",
    "Dumbbell bicep curl": "Biceps",
    "Single-arm shoulder raise": "Shoulders",
    "Seated shoulder press": "Shoulders",
    "Lat pulldown": "Back",
    "Seated row": "Back",
    "Tricep pulldown": "Triceps",
    "Overhead dumbbell tricep extension": "Triceps",
    "Pull-up": "Back",
    "Rear delt machine": "Shoulders",
    "Leg extension": "Legs",
    "Incline bench press": "Chest",
    "Incline T-bar row": "Back",
    "Leg press": "Legs",
    "Leg press calf raise": "Legs",
    "Cycling": "Cardio",
}

MUSCLE_GROUPS = [
    "Chest",
    "Back",
    "Shoulders",
    "Biceps",
    "Triceps",
    "Legs",
    "Core",
    "Cardio",
    "Full body",
]

MUSCLE_TARGETS = {
    "bench press": {
        "Chest": 1.0,
        "Front delts": 0.45,
        "Triceps": 0.45,
    },
    "incline bench press": {
        "Upper chest": 1.0,
        "Chest": 0.65,
        "Front delts": 0.55,
        "Triceps": 0.4,
    },
    "seated lateral raise machine": {
        "Side delts": 1.0,
        "Traps": 0.2,
    },
    "single-arm shoulder raise": {
        "Side delts": 1.0,
        "Front delts": 0.25,
        "Traps": 0.15,
    },
    "seated shoulder press": {
        "Front delts": 1.0,
        "Side delts": 0.55,
        "Triceps": 0.55,
        "Upper chest": 0.2,
    },
    "barbell bicep curl": {
        "Biceps": 1.0,
        "Forearms": 0.35,
    },
    "dumbbell bicep curl": {
        "Biceps": 1.0,
        "Forearms": 0.35,
    },
    "lat pulldown": {
        "Lats": 1.0,
        "Upper back": 0.45,
        "Biceps": 0.45,
        "Rear delts": 0.2,
    },
    "seated row": {
        "Upper back": 1.0,
        "Lats": 0.7,
        "Rear delts": 0.45,
        "Biceps": 0.4,
    },
    "pull-up": {
        "Lats": 1.0,
        "Upper back": 0.45,
        "Biceps": 0.45,
        "Core": 0.2,
    },
    "tricep pulldown": {
        "Triceps": 1.0,
    },
    "overhead dumbbell tricep extension": {
        "Triceps": 1.0,
    },
    "rear delt machine": {
        "Rear delts": 1.0,
        "Upper back": 0.35,
        "Traps": 0.25,
    },
    "leg extension": {
        "Quads": 1.0,
    },
    "leg press": {
        "Quads": 1.0,
        "Glutes": 0.65,
        "Hamstrings": 0.35,
        "Calves": 0.15,
    },
    "leg press calf raise": {
        "Calves": 1.0,
    },
    "incline t-bar row": {
        "Upper back": 1.0,
        "Lats": 0.65,
        "Rear delts": 0.5,
        "Biceps": 0.35,
        "Traps": 0.25,
    },
    "cycling": {
        "Cardio": 1.0,
        "Quads": 0.45,
        "Glutes": 0.25,
        "Calves": 0.25,
        "Hamstrings": 0.15,
    },
}

MUSCLE_SECTIONS = {
    "Push": ["Chest", "Upper chest", "Front delts", "Side delts", "Triceps"],
    "Pull": ["Lats", "Upper back", "Rear delts", "Traps", "Biceps", "Forearms"],
    "Legs / Core": ["Quads", "Hamstrings", "Glutes", "Calves", "Core"],
    "Conditioning": ["Cardio"],
}

ALL_TRACKED_MUSCLES = [muscle for muscles in MUSCLE_SECTIONS.values() for muscle in muscles]

COLUMNS = [
    "date",
    "start_time",
    "session_type",
    "exercise",
    "muscle_group",
    "sets",
    "reps",
    "weight_kg",
    "weight_basis",
    "rpe",
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
    "notes",
]

COLUMN_ALIASES = {
    "date": "date",
    "workout date": "date",
    "start time": "start_time",
    "session": "session_type",
    "session type": "session_type",
    "exercise": "exercise",
    "exercise name": "exercise",
    "other exercise": "other_exercise",
    "muscle group": "muscle_group",
    "sets": "sets",
    "reps": "reps",
    "weight kg": "weight_kg",
    "weight (kg)": "weight_kg",
    "weight_kg": "weight_kg",
    "weight basis": "weight_basis",
    "rpe": "rpe",
    "duration min": "duration_min",
    "duration (min)": "duration_min",
    "calories": "calories",
    "avg heart rate": "avg_heart_rate",
    "average heart rate": "avg_heart_rate",
    "max heart rate": "max_heart_rate",
    "body weight kg": "body_weight_kg",
    "body weight (kg)": "body_weight_kg",
    "protein taken": "protein_taken",
    "took protein": "protein_taken",
    "protein grams": "protein_grams",
    "energy": "energy",
    "motivation": "motivation",
    "session quality": "session_quality",
    "gym session quality": "session_quality",
    "productivity": "productivity",
    "felt productive": "productivity",
    "sleep hours": "sleep_hours",
    "sleep (hours)": "sleep_hours",
    "feeling": "feeling",
    "how i am feeling": "feeling",
    "how im feeling": "feeling",
    "notes": "notes",
}


def canonical_label(value: object) -> str:
    return str(value).strip().lower()


def row_value(row: pd.Series, lookup: dict[str, str], *labels: str) -> object:
    for label in labels:
        column = lookup.get(canonical_label(label))
        if column is not None:
            return row.get(column)
    return None


def is_filled(value: object) -> bool:
    if pd.isna(value):
        return False
    return str(value).strip() != ""


def detect_exercise_name(value: object) -> str:
    if not is_filled(value):
        return ""

    raw = str(value).strip()
    normalized = canonical_label(raw).replace("-", " ")
    compact = " ".join(normalized.split())

    if ("calf" in compact or "calves" in compact) and "leg press" in compact:
        return "Leg press calf raise"
    if "leg press" in compact:
        return "Leg press"
    if "incline" in compact and ("bench" in compact or "press" in compact):
        return "Incline bench press"
    if "inclined" in compact and ("bench" in compact or "press" in compact):
        return "Incline bench press"

    for exercise in EXERCISES:
        if canonical_label(exercise) == compact:
            return exercise

    return raw


def expand_multi_exercise_form(df: pd.DataFrame) -> pd.DataFrame:
    lookup = {canonical_label(column): column for column in df.columns}
    has_multi_exercise_columns = any(canonical_label(f"Exercise {index}") in lookup for index in range(1, 7))
    if not has_multi_exercise_columns:
        return df

    rows = []
    for _, form_row in df.iterrows():
        entry_type = row_value(form_row, lookup, "Entry type")
        session_fields = {
            "date": row_value(form_row, lookup, "Date", "Workout date"),
            "start_time": row_value(form_row, lookup, "Start time"),
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
    weight = row.get("weight_kg")
    if pd.isna(reps) or pd.isna(weight) or reps <= 0 or weight <= 0:
        return 0.0
    return round(float(weight) * (1 + float(reps) / 30), 1)


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
    missing_group = df["muscle_group"].isna() | (df["muscle_group"].fillna("").astype(str).str.strip() == "")
    df.loc[missing_group, "muscle_group"] = df.loc[missing_group, "exercise"].map(EXERCISES).fillna("Full body")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
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

    df["volume_kg"] = df["sets"].fillna(0) * df["reps"].fillna(0) * df["weight_kg"].fillna(0)
    df["estimated_1rm_kg"] = df.apply(estimate_one_rep_max, axis=1)
    return df


@st.cache_data(ttl=60)
def read_google_sheet_csv(sheet_url: str) -> pd.DataFrame:
    return pd.read_csv(to_google_sheet_csv_url(sheet_url))


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
    gid = query.get("gid", fragment_query.get("gid", ["0"]))[0]
    return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid={gid}"


def load_workouts(csv_url: str | None = None) -> pd.DataFrame:
    ensure_data_file()
    local_df = normalize_workouts(pd.read_csv(WORKOUTS_PATH))
    if csv_url:
        try:
            sheet_df = normalize_workouts(read_google_sheet_csv(csv_url))
            combined = pd.concat([local_df, sheet_df], ignore_index=True)
            dedupe_columns = ["date", "exercise", "sets", "reps", "weight_kg", "weight_basis", "notes"]
            return combined.drop_duplicates(subset=dedupe_columns, keep="last").reset_index(drop=True)
        except Exception as exc:
            st.sidebar.error(f"Could not load Google Sheet CSV: {exc}")
            st.sidebar.info("Make sure the sheet is shared as 'Anyone with the link can view' or published to the web.")

    return local_df


def append_workout(row: dict) -> None:
    ensure_data_file()
    df = pd.read_csv(WORKOUTS_PATH)
    for column in COLUMNS:
        if column not in df.columns:
            df[column] = None
    df = df[COLUMNS]
    df = pd.concat([df, pd.DataFrame([row], columns=COLUMNS)], ignore_index=True)
    df.to_csv(WORKOUTS_PATH, index=False)


def format_set_target(row: pd.Series) -> str:
    sets = "?" if pd.isna(row["sets"]) else f"{row['sets']:.0f}"
    reps = "?" if pd.isna(row["reps"]) else f"{row['reps']:.0f}"
    weight = "?" if pd.isna(row["weight_kg"]) else f"{row['weight_kg']:.1f} kg"
    return f"{sets} x {reps} @ {weight}"


def format_current_target(row: pd.Series) -> str:
    if pd.isna(row["reps"]):
        return f"{row['sets']:.0f} sets @ {row['weight_kg']:.1f} kg"
    return format_set_target(row)


def get_muscle_targets(row: pd.Series) -> dict[str, float]:
    exercise = str(row.get("exercise", "")).strip().lower()
    if exercise in MUSCLE_TARGETS:
        return MUSCLE_TARGETS[exercise]

    group = row.get("muscle_group")
    if pd.isna(group) or not str(group).strip():
        return {"Unmapped": 1.0}
    return {str(group).strip(): 1.0}


def build_muscle_target_table(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, workout in df.dropna(subset=["date"]).iterrows():
        sets = 0 if pd.isna(workout["sets"]) else float(workout["sets"])
        volume = 0 if pd.isna(workout["volume_kg"]) else float(workout["volume_kg"])
        for muscle, emphasis in get_muscle_targets(workout).items():
            rows.append(
                {
                    "date": workout["date"],
                    "exercise": workout["exercise"],
                    "muscle": muscle,
                    "target_sets": sets * emphasis,
                    "target_volume": volume * emphasis,
                    "emphasis": emphasis,
                }
            )

    return pd.DataFrame(rows, columns=["date", "exercise", "muscle", "target_sets", "target_volume", "emphasis"])


def canonicalize_muscle_column(df: pd.DataFrame, target_name: str) -> pd.DataFrame:
    df = df.copy()
    if target_name == "muscle" and "Muscle" in df.columns and "muscle" not in df.columns:
        return df.rename(columns={"Muscle": "muscle"})
    if target_name == "Muscle" and "muscle" in df.columns and "Muscle" not in df.columns:
        return df.rename(columns={"muscle": "Muscle"})
    if target_name not in df.columns:
        df[target_name] = pd.Series(dtype="object")
    return df


def build_next_muscle_suggestions(df: pd.DataFrame) -> pd.DataFrame:
    summary = build_muscle_summary(df)
    summary = canonicalize_muscle_column(summary, "Muscle")
    if summary.empty:
        return summary

    summary["Need score"] = summary["Days ago"].fillna(99) * 1.5 + (8 - summary["Target sets, 14d"]).clip(lower=0)
    return summary.sort_values("Need score", ascending=False)


def build_muscle_summary(df: pd.DataFrame) -> pd.DataFrame:
    targets = build_muscle_target_table(df)
    targets = canonicalize_muscle_column(targets, "muscle")
    if targets.empty:
        return pd.DataFrame(columns=["Muscle", "Last hit", "Days ago", "Target sets, 14d", "Coverage"])

    latest_day = targets["date"].max()
    recent = targets[targets["date"] >= latest_day - pd.Timedelta(days=14)]
    recent_sets = recent.groupby("muscle")["target_sets"].sum()
    last_hit = targets.groupby("muscle")["date"].max()

    muscles = sorted(set(ALL_TRACKED_MUSCLES) | set(targets["muscle"].dropna().unique()))
    summary = pd.DataFrame({"Muscle": muscles})
    summary["Last hit"] = summary["Muscle"].map(last_hit)
    summary["Days ago"] = (latest_day - summary["Last hit"]).dt.days
    summary["Target sets, 14d"] = summary["Muscle"].map(recent_sets).fillna(0)
    summary["Coverage"] = (summary["Target sets, 14d"] / 8).clip(upper=1)
    return summary


def muscle_status(row: pd.Series) -> str:
    if pd.isna(row["Days ago"]):
        return "untouched"
    if row["Target sets, 14d"] >= 8:
        return "covered"
    if row["Target sets, 14d"] >= 4:
        return "light"
    return "due"


def muscle_tile_html(row: pd.Series) -> str:
    muscle_name = row.get("Muscle", row.name)
    status = muscle_status(row)
    days_label = "never" if pd.isna(row["Days ago"]) else f"{int(row['Days ago'])}d ago"
    sets_label = f"{row['Target sets, 14d']:.1f} sets"
    coverage = int(row["Coverage"] * 100)
    colors = {
        "covered": ("#176f4d", "#dff5eb"),
        "light": ("#9a5b00", "#fff1c7"),
        "due": ("#a13f2a", "#ffe3dc"),
        "untouched": ("#6b7280", "#f3f4f6"),
    }
    accent, background = colors[status]
    return f"""
        <div class="muscle-tile" style="background:{background}; border-color:{accent};">
            <div class="muscle-topline">
                <span class="muscle-name">{escape(str(muscle_name))}</span>
                <span class="muscle-status" style="color:{accent};">{status}</span>
            </div>
            <div class="muscle-meta">{sets_label} · {days_label}</div>
            <div class="muscle-meter"><span style="width:{coverage}%; background:{accent};"></span></div>
        </div>
    """


def format_days_ago(value: object) -> str:
    if pd.isna(value):
        return "never"
    return f"{int(value)}d ago"


def render_muscle_heatmap(summary: pd.DataFrame) -> None:
    summary = canonicalize_muscle_column(summary, "Muscle")
    if "Muscle" not in summary.columns:
        st.info("Muscle summary is unavailable for this data source.")
        return

    lookup = summary.set_index("Muscle")
    sections = []
    for section, muscles in MUSCLE_SECTIONS.items():
        tiles = []
        for muscle in muscles:
            row = lookup.loc[muscle] if muscle in lookup.index else pd.Series(
                {"Muscle": muscle, "Days ago": pd.NA, "Target sets, 14d": 0, "Coverage": 0}
            )
            tiles.append(muscle_tile_html(row))

        sections.append(
            f"""
            <section class="muscle-section">
                <h4>{escape(section)}</h4>
                <div class="muscle-grid">{''.join(tiles)}</div>
            </section>
            """
        )

    html = f"""
        <style>
            body {{
                margin: 0;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            }}
            .muscle-board {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
                gap: 14px;
                margin: 8px 0 18px;
            }}
            .muscle-section {{
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 12px;
                background: #ffffff;
            }}
            .muscle-section h4 {{
                margin: 0 0 10px;
                font-size: 0.95rem;
            }}
            .muscle-grid {{
                display: grid;
                gap: 8px;
            }}
            .muscle-tile {{
                border-left: 5px solid;
                border-radius: 8px;
                padding: 9px 10px;
            }}
            .muscle-topline {{
                align-items: center;
                display: flex;
                justify-content: space-between;
                gap: 8px;
            }}
            .muscle-name {{
                color: #111827;
                font-weight: 650;
                font-size: 0.92rem;
            }}
            .muscle-status {{
                font-size: 0.75rem;
                font-weight: 700;
                text-transform: uppercase;
            }}
            .muscle-meta {{
                color: #4b5563;
                font-size: 0.8rem;
                margin-top: 3px;
            }}
            .muscle-meter {{
                background: rgba(255,255,255,0.8);
                border-radius: 999px;
                height: 5px;
                margin-top: 8px;
                overflow: hidden;
            }}
            .muscle-meter span {{
                display: block;
                height: 100%;
            }}
        </style>
        <div class="muscle-board">{''.join(sections)}</div>
    """
    component_height = 210 * len(MUSCLE_SECTIONS)
    components.html(html, height=component_height, scrolling=False)


def render_muscle_target_visual(df: pd.DataFrame) -> None:
    summary = build_muscle_summary(df)
    summary = canonicalize_muscle_column(summary, "Muscle")
    if summary.empty:
        st.info("Log exercises to unlock muscle target analysis.")
        return

    st.markdown("**Muscle coverage, last 14 days**")
    render_muscle_heatmap(summary)

    suggestions = build_next_muscle_suggestions(df).head(6)
    st.markdown("**What looks most due**")
    st.dataframe(
        suggestions[["Muscle", "Days ago", "Target sets, 14d"]].round({"Target sets, 14d": 1}),
        hide_index=True,
        use_container_width=True,
    )


def render_muscle_trends(df: pd.DataFrame) -> None:
    st.subheader("Muscle trends")

    targets = build_muscle_target_table(df)
    if targets.empty:
        st.info("Log exercises to unlock muscle trend charts.")
        return

    targets = targets.dropna(subset=["date"])
    section_options = ["All", *MUSCLE_SECTIONS.keys()]
    selected_section = st.segmented_control("Group", section_options, default="All")

    available_muscles = sorted(targets["muscle"].dropna().unique())
    default_muscles = (
        available_muscles[:8]
        if selected_section == "All"
        else [muscle for muscle in MUSCLE_SECTIONS[selected_section] if muscle in available_muscles]
    )

    selected_muscles = st.multiselect(
        "Muscles",
        available_muscles,
        default=default_muscles,
        help="Weighted target sets count primary muscles more than secondary helpers.",
    )

    if not selected_muscles:
        st.info("Choose at least one muscle.")
        return

    filtered = targets[targets["muscle"].isin(selected_muscles)].copy()
    cadence = st.radio("Time bucket", ["Daily", "Weekly"], horizontal=True)
    freq = "D" if cadence == "Daily" else "W-MON"

    trend = (
        filtered.set_index("date")
        .groupby("muscle")["target_sets"]
        .resample(freq)
        .sum()
        .reset_index()
        .pivot(index="date", columns="muscle", values="target_sets")
        .fillna(0)
        .sort_index()
    )

    rolling_window = 3 if cadence == "Daily" else 2
    smoothed = trend.rolling(rolling_window, min_periods=1).mean()

    st.markdown("**Weighted target sets over time**")
    st.line_chart(smoothed, use_container_width=True)

    latest = build_muscle_summary(df)
    latest = latest[latest["Muscle"].isin(selected_muscles)].sort_values("Target sets, 14d", ascending=False)

    st.markdown("**Current 14-day picture**")
    st.dataframe(
        latest[["Muscle", "Days ago", "Target sets, 14d", "Coverage"]].round(
            {"Target sets, 14d": 1, "Coverage": 2}
        ),
        hide_index=True,
        use_container_width=True,
    )


def render_log_form() -> None:
    st.subheader("Quick log")
    st.caption("Use this between exercises. Log the lift first; add recovery details later if you have them.")

    with st.form("workout_form", clear_on_submit=True):
        left, right = st.columns(2)
        workout_date = left.date_input("Date", value=date.today())
        start_time = right.time_input("Start time", value=datetime.now().time().replace(second=0, microsecond=0))

        session_type = left.selectbox("Session", ["Upper", "Push", "Pull", "Arms", "Full body", "Other"])
        exercise_choice = right.selectbox("Exercise", sorted(EXERCISES) + ["Custom"])

        if exercise_choice == "Custom":
            exercise = st.text_input("Custom exercise")
            default_group = "Full body"
        else:
            exercise = exercise_choice
            default_group = EXERCISES[exercise_choice]

        muscle_group = st.selectbox("Muscle group", MUSCLE_GROUPS, index=MUSCLE_GROUPS.index(default_group))

        sets_col, reps_col, weight_col = st.columns(3)
        sets = sets_col.number_input("Sets", min_value=1, max_value=20, value=4, step=1)
        reps_known = reps_col.checkbox("Know reps", value=True)
        reps = None
        if reps_known:
            reps = reps_col.number_input("Reps", min_value=1, max_value=100, value=10, step=1)
        weight = weight_col.number_input("Weight (kg)", min_value=0.0, max_value=500.0, value=20.0, step=0.5)
        weight_basis = st.selectbox("Weight basis", ["total", "per hand", "per side", "bodyweight"])

        rpe_col, energy_col = st.columns(2)
        rpe_known = rpe_col.checkbox("Add RPE", value=False)
        rpe = rpe_col.slider("RPE", min_value=1, max_value=10, value=7) if rpe_known else None
        energy_known = energy_col.checkbox("Add energy", value=False)
        energy = energy_col.slider("Energy", min_value=1, max_value=10, value=7) if energy_known else None

        with st.expander("Optional session details"):
            duration_col, calories_col, body_col = st.columns(3)
            duration = duration_col.number_input("Duration (min)", min_value=0, max_value=300, value=0, step=5)
            calories = calories_col.number_input("Calories", min_value=0, max_value=3000, value=0, step=10)
            body_weight = body_col.number_input("Body weight (kg)", min_value=0.0, max_value=250.0, value=0.0, step=0.1)

            hr_col, max_hr_col, sleep_col = st.columns(3)
            avg_heart_rate = hr_col.number_input("Avg heart rate", min_value=0, max_value=240, value=0, step=1)
            max_heart_rate = max_hr_col.number_input("Max heart rate", min_value=0, max_value=240, value=0, step=1)
            sleep_hours = sleep_col.number_input("Sleep (hours)", min_value=0.0, max_value=16.0, value=0.0, step=0.25)

            protein_col, grams_col = st.columns(2)
            protein_taken = protein_col.checkbox("Took protein")
            protein_grams = grams_col.number_input("Protein grams", min_value=0, max_value=250, value=0, step=5)

            mood_col, quality_col, motivation_col = st.columns(3)
            session_quality = quality_col.slider("Session quality", min_value=1, max_value=10, value=7)
            motivation = motivation_col.slider("Motivation", min_value=1, max_value=10, value=7)
            productivity = mood_col.slider("Productivity", min_value=1, max_value=10, value=7)
            feeling = st.text_input("How you are feeling", placeholder="Really tired, sleep deprived, focused, stressed...")

        notes = st.text_area("Notes", placeholder="Form cues, pain, next target, mood, anything useful...")
        submitted = st.form_submit_button("Save workout")

    if not submitted:
        return

    if not exercise.strip():
        st.error("Add an exercise name before saving.")
        return

    append_workout(
        {
            "date": workout_date.isoformat(),
            "start_time": start_time.strftime("%H:%M") if isinstance(start_time, time) else str(start_time),
            "session_type": session_type,
            "exercise": exercise.strip(),
            "muscle_group": muscle_group,
            "sets": sets,
            "reps": reps if reps_known else None,
            "weight_kg": weight,
            "weight_basis": weight_basis,
            "rpe": rpe,
            "duration_min": duration if duration > 0 else None,
            "calories": calories if calories > 0 else None,
            "avg_heart_rate": avg_heart_rate if avg_heart_rate > 0 else None,
            "max_heart_rate": max_heart_rate if max_heart_rate > 0 else None,
            "body_weight_kg": body_weight if body_weight > 0 else None,
            "protein_taken": protein_taken,
            "protein_grams": protein_grams if protein_grams > 0 else None,
            "energy": energy,
            "motivation": motivation,
            "session_quality": session_quality,
            "productivity": productivity,
            "sleep_hours": sleep_hours if sleep_hours > 0 else None,
            "feeling": feeling.strip(),
            "notes": notes.strip(),
        }
    )
    st.success("Workout saved.")
    st.rerun()


def render_progress(df: pd.DataFrame) -> None:
    st.subheader("Progress")

    if df.empty:
        st.info("Log your first workout to unlock progress charts.")
        return

    df = df.dropna(subset=["date"]).sort_values("date")
    exercise_options = sorted(df["exercise"].dropna().unique())
    selected = st.selectbox("Exercise", exercise_options, key="progress_exercise")
    metric_label = st.segmented_control(
        "Metric",
        ["Weight", "Volume", "Estimated 1RM", "Reps"],
        default="Weight",
    )

    metric_map = {
        "Weight": "weight_kg",
        "Volume": "volume_kg",
        "Estimated 1RM": "estimated_1rm_kg",
        "Reps": "reps",
    }
    metric = metric_map[metric_label]
    exercise_df = df[df["exercise"] == selected].copy()
    chart_df = exercise_df.dropna(subset=[metric])

    if chart_df.empty or chart_df[metric].sum() == 0:
        st.warning("This exercise needs reps or weight recorded before this metric becomes useful.")
    else:
        daily = (
            chart_df.groupby("date", as_index=False)
            .agg(
                weight_kg=("weight_kg", "max"),
                volume_kg=("volume_kg", "sum"),
                estimated_1rm_kg=("estimated_1rm_kg", "max"),
                reps=("reps", "max"),
            )
            .sort_values("date")
        )
        daily["trend"] = daily[metric].rolling(3, min_periods=1).mean()

        st.line_chart(daily, x="date", y=[metric, "trend"], use_container_width=True)

        best = daily.loc[daily[metric].idxmax()]
        latest = daily.iloc[-1]
        cols = st.columns(3)
        cols[0].metric("Latest", f"{latest[metric]:,.1f}")
        cols[1].metric("Best", f"{best[metric]:,.1f}", best["date"].strftime("%b %d"))
        cols[2].metric("Entries", len(exercise_df))

    st.markdown("**History for this lift**")
    history = exercise_df.sort_values("date", ascending=False).copy()
    history["date"] = history["date"].dt.strftime("%Y-%m-%d")
    st.dataframe(
        history[
            [
                "date",
                "sets",
                "reps",
                "weight_kg",
                "weight_basis",
                "volume_kg",
                "estimated_1rm_kg",
                "rpe",
                "notes",
            ]
        ],
        hide_index=True,
        use_container_width=True,
    )


def render_dashboard(df: pd.DataFrame) -> None:
    st.subheader("Dashboard")

    if df.empty:
        st.info("Log your first workout to unlock charts.")
        return

    df = df.dropna(subset=["date"]).sort_values("date")
    latest_day = df["date"].max()
    recent = df[df["date"] >= latest_day - pd.Timedelta(days=30)]

    cols = st.columns(4)
    cols[0].metric("Workout days", df["date"].dt.date.nunique())
    cols[1].metric("Total sets", int(df["sets"].sum()))
    cols[2].metric("Total volume", f"{df['volume_kg'].sum():,.0f} kg")
    avg_rpe = df["rpe"].mean()
    cols[3].metric("Avg RPE", f"{avg_rpe:.1f}/10" if not pd.isna(avg_rpe) else "-")

    st.divider()

    volume_col, muscle_col = st.columns([1.15, 1])
    with volume_col:
        st.markdown("**Volume by week**")
        weekly = (
            df.set_index("date")
            .resample("W-MON")["volume_kg"]
            .sum()
            .reset_index()
            .rename(columns={"date": "week"})
        )
        st.bar_chart(weekly, x="week", y="volume_kg", use_container_width=True)

    with muscle_col:
        st.markdown("**Sets by muscle group, last 30 days**")
        muscle_sets = recent.groupby("muscle_group")["sets"].sum().sort_values(ascending=False).reset_index()
        st.bar_chart(muscle_sets, x="muscle_group", y="sets", use_container_width=True)

    st.divider()
    render_muscle_target_visual(df)

    progress_col, recency_col = st.columns([1.15, 1])
    with progress_col:
        st.markdown("**Exercise progress**")
        selected = st.selectbox("Exercise", sorted(df["exercise"].dropna().unique()))
        exercise_df = df[df["exercise"] == selected].sort_values("date")
        st.line_chart(exercise_df, x="date", y=["weight_kg", "estimated_1rm_kg"], use_container_width=True)
        st.caption("Estimated 1RM uses weight x (1 + reps / 30).")

    with recency_col:
        st.markdown("**Muscle group recency**")
        recency = df.groupby("muscle_group")["date"].max().reset_index()
        recency["days_ago"] = (latest_day - recency["date"]).dt.days
        recency = recency.sort_values("days_ago", ascending=False)
        st.dataframe(
            recency.rename(
                columns={
                    "muscle_group": "Muscle group",
                    "date": "Last trained",
                    "days_ago": "Days ago",
                }
            ),
            hide_index=True,
            use_container_width=True,
        )

    st.divider()
    st.markdown("**Recent entries**")
    table = df.sort_values("date", ascending=False).head(30).copy()
    table["date"] = table["date"].dt.strftime("%Y-%m-%d")
    st.dataframe(
        table[
            [
                "date",
                "start_time",
                "session_type",
                "exercise",
                "muscle_group",
                "sets",
                "reps",
                "weight_kg",
                "weight_basis",
                "volume_kg",
                "rpe",
                "notes",
            ]
        ],
        hide_index=True,
        use_container_width=True,
    )


def render_gym_view(df: pd.DataFrame) -> None:
    st.subheader("Gym view")

    if df.empty:
        st.info("Log one workout first, then this view becomes your quick check-in screen.")
        return

    df = df.dropna(subset=["date"]).sort_values("date")
    latest_day = df["date"].max()

    st.markdown("**Train today?**")
    muscle_suggestions = build_next_muscle_suggestions(df)
    stale_groups = muscle_suggestions.head(3)

    suggestion = stale_groups.iloc[0]
    st.metric(
        "Most due muscle",
        suggestion["Muscle"],
        f"{format_days_ago(suggestion['Days ago'])} since last hit",
    )

    cols = st.columns(3)
    for index, row in stale_groups.reset_index(drop=True).iterrows():
        cols[index].metric(row["Muscle"], format_days_ago(row["Days ago"]))

    render_muscle_target_visual(df)

    st.divider()

    st.markdown("**Last time you did each lift**")
    last_lifts = (
        df.sort_values("date")
        .groupby("exercise")
        .tail(1)
        .sort_values("date", ascending=False)
        .copy()
    )
    last_lifts["Last done"] = last_lifts["date"].dt.strftime("%b %d")
    last_lifts["Set target"] = last_lifts.apply(format_set_target, axis=1)
    st.dataframe(
        last_lifts[["exercise", "muscle_group", "Last done", "Set target", "rpe"]].rename(
            columns={
                "exercise": "Exercise",
                "muscle_group": "Group",
                "rpe": "RPE",
            }
        ),
        hide_index=True,
        use_container_width=True,
    )

    st.divider()

    st.markdown("**Simple next targets**")
    targets = []
    for exercise, exercise_df in df.groupby("exercise"):
        best = exercise_df.sort_values(["estimated_1rm_kg", "date"], ascending=[False, False]).iloc[0]
        latest = exercise_df.sort_values("date").iloc[-1]
        targets.append(
            {
                "Exercise": exercise,
                "Current": format_current_target(latest),
                "Best est. 1RM": f"{best['estimated_1rm_kg']:.1f} kg",
                "Nudge": build_next_target(latest),
            }
        )

    st.dataframe(pd.DataFrame(targets), hide_index=True, use_container_width=True)

    st.divider()
    st.markdown("**Fast logging rule**")
    st.write("During the workout, log one row after each exercise: exercise, sets, reps, weight. Everything else can wait.")


def build_next_target(row: pd.Series) -> str:
    if pd.isna(row["reps"]):
        return "Record reps next time"
    if pd.isna(row["rpe"]):
        return "Add RPE next time"
    if row["rpe"] <= 7:
        return f"Try {row['weight_kg'] + 2.5:.1f} kg or add reps"
    if row["rpe"] >= 9:
        return "Hold weight and clean up reps"
    return "Add 1 rep before adding weight"


def render_setup(csv_url: str | None) -> None:
    st.subheader("Google Form setup")

    st.markdown("**What this gives you**")
    st.write("Use Google Forms on your phone at the gym. This dashboard can read the linked Google Sheet afterward.")

    st.markdown("**Create the form**")
    st.write("Open the script below in Google Apps Script, run `createTrainingLabForm`, and it will create a Google Form plus linked response sheet.")
    st.code(str(FORM_SCRIPT_PATH), language="text")

    st.markdown("**Connect the sheet**")
    st.write("After responses start coming in, publish or export the response sheet as CSV and paste that CSV URL into the sidebar.")
    if csv_url:
        st.success("Google Sheet CSV is active.")
    else:
        st.info("No Google Sheet CSV URL yet. The app is currently using the local CSV.")
    st.warning("The response sheet must be shared as 'Anyone with the link can view' or published to the web before Streamlit can read it.")

    st.markdown("**Gym logging rule**")
    st.code(
        "1 form submission = 1 gym session\n"
        "Fill up to 6 exercise blocks as you go\n"
        "Exercise 1 is required; exercises 2-6 are optional\n"
        "Shared optional details: duration, calories, heart rate, protein, body weight, feeling, motivation, session quality, notes",
        language="text",
    )


def render_data(df: pd.DataFrame) -> None:
    st.subheader("Data")
    st.caption(str(WORKOUTS_PATH))

    export = df.copy()
    if not export.empty:
        export["date"] = export["date"].dt.strftime("%Y-%m-%d")
    st.dataframe(export, hide_index=True, use_container_width=True)
    st.download_button("Download CSV", WORKOUTS_PATH.read_text(), "workouts.csv", "text/csv")


def render_mappings() -> None:
    st.subheader("Exercise to muscle mapping")
    st.caption("Weighted target sets use 1.0 for primary muscles and smaller values for secondary muscles.")

    rows = []
    for exercise, default_group in sorted(EXERCISES.items()):
        targets = MUSCLE_TARGETS.get(canonical_label(exercise), {default_group: 1.0})
        rows.append(
            {
                "Exercise": exercise,
                "Default group": default_group,
                "Primary targets": ", ".join(muscle for muscle, weight in targets.items() if weight >= 0.75),
                "Secondary targets": ", ".join(
                    f"{muscle} ({weight:g})" for muscle, weight in targets.items() if weight < 0.75
                ),
            }
        )

    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

    st.markdown("**Raw mapping weights**")
    raw_rows = []
    for exercise, targets in sorted(MUSCLE_TARGETS.items()):
        for muscle, weight in targets.items():
            raw_rows.append({"Exercise": exercise, "Muscle": muscle, "Weight": weight})
    st.dataframe(pd.DataFrame(raw_rows), hide_index=True, use_container_width=True)


def main() -> None:
    st.set_page_config(page_title="Training Lab", page_icon=":material/fitness_center:", layout="wide")
    st.title("Training Lab")
    st.caption("Log the lifts you actually do, then watch consistency, volume, and strength trends.")

    st.sidebar.header("Data source")
    google_sheet_url = st.sidebar.text_input(
        "Google Sheet URL",
        value=DEFAULT_GOOGLE_SHEET_URL,
        placeholder="https://docs.google.com/spreadsheets/d/.../edit?gid=...",
    ).strip()
    csv_url = google_sheet_url or None
    st.sidebar.caption(f"Using: {'Google Sheet' if csv_url else 'Local CSV'}")
    if csv_url:
        st.sidebar.caption(f"CSV export: {to_google_sheet_csv_url(csv_url)}")

    df = load_workouts(csv_url)
    gym_tab, log_tab, progress_tab, muscle_trends_tab, dashboard_tab, setup_tab, data_tab, mappings_tab = st.tabs(
        ["Gym view", "Log workout", "Progress", "Muscle trends", "Dashboard", "Setup", "Data", "Mappings"]
    )

    with gym_tab:
        render_gym_view(df)
    with log_tab:
        render_log_form()
    with progress_tab:
        render_progress(df)
    with muscle_trends_tab:
        render_muscle_trends(df)
    with dashboard_tab:
        render_dashboard(df)
    with setup_tab:
        render_setup(csv_url)
    with data_tab:
        render_data(df)
    with mappings_tab:
        render_mappings()


if __name__ == "__main__":
    main()
