from __future__ import annotations

import pandas as pd

from .config import ALL_TRACKED_MUSCLES, MUSCLE_TARGETS

def format_set_target(row: pd.Series) -> str:
    sets = "?" if pd.isna(row["sets"]) else f"{row['sets']:.0f}"
    reps = "?" if pd.isna(row["reps"]) else f"{row['reps']:.0f}"
    weight = "?" if pd.isna(row["load_kg"]) else f"{row['load_kg']:.1f} kg load"
    return f"{sets} x {reps} @ {weight}"


def format_current_target(row: pd.Series) -> str:
    if pd.isna(row["reps"]):
        return f"{row['sets']:.0f} sets @ {row['load_kg']:.1f} kg load"
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
