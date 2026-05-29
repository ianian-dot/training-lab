from __future__ import annotations

import pandas as pd

from .config import ALL_TRACKED_MUSCLES, MUSCLE_TARGETS


def workout_rows(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    return df[df["exercise"].fillna("") != "Session update"].copy()


def session_days(df: pd.DataFrame) -> pd.Series:
    workouts = workout_rows(df).dropna(subset=["date"])
    if workouts.empty:
        return pd.Series(dtype="datetime64[ns]")
    days = pd.to_datetime(workouts["date"]).dt.normalize().drop_duplicates().sort_values()
    return days.reset_index(drop=True)


def weekly_session_counts(df: pd.DataFrame) -> pd.DataFrame:
    days = session_days(df)
    if days.empty:
        return pd.DataFrame(columns=["week_start", "sessions"])

    weekly = pd.DataFrame({"date": days, "sessions": 1})
    weekly["week_start"] = weekly["date"].dt.to_period("W-SUN").apply(lambda value: value.start_time)
    return weekly.groupby("week_start", as_index=False)["sessions"].sum()


def rest_day_summary(df: pd.DataFrame) -> dict[str, float | int | None]:
    days = session_days(df)
    if days.empty:
        return {"sessions": 0, "avg_gap_days": None, "avg_rest_days": None, "longest_rest_days": None}
    if len(days) == 1:
        return {"sessions": 1, "avg_gap_days": None, "avg_rest_days": None, "longest_rest_days": None}

    gaps = days.diff().dropna().dt.days
    rest_days = (gaps - 1).clip(lower=0)
    return {
        "sessions": int(len(days)),
        "avg_gap_days": float(gaps.mean()),
        "avg_rest_days": float(rest_days.mean()),
        "longest_rest_days": int(rest_days.max()),
    }


def cost_summary(df: pd.DataFrame, monthly_fee: float) -> dict[str, float | int | None]:
    days = session_days(df)
    if days.empty or monthly_fee <= 0:
        return {"months": 0, "total_cost": 0.0, "cost_per_session": None}

    first_month = days.min().to_period("M")
    latest_month = days.max().to_period("M")
    months = len(pd.period_range(first_month, latest_month, freq="M"))
    total_cost = float(months * monthly_fee)
    return {
        "months": int(months),
        "total_cost": total_cost,
        "cost_per_session": total_cost / len(days),
    }


def current_month_summary(
    df: pd.DataFrame,
    monthly_fee: float,
    target_cost_per_session: float,
) -> dict[str, float | int | str | None]:
    days = session_days(df)
    if days.empty:
        return {
            "month": "-",
            "sessions": 0,
            "cost_per_session": None,
            "target_sessions": 0,
            "sessions_to_target": 0,
            "remaining_days": 0,
            "pace_per_week": None,
        }

    latest_day = days.max()
    current_month = latest_day.to_period("M")
    month_days = days[days.dt.to_period("M") == current_month]
    sessions = int(len(month_days))
    cost_per_session = monthly_fee / sessions if sessions and monthly_fee > 0 else None
    target_sessions = (
        int(-(-monthly_fee // target_cost_per_session))
        if monthly_fee > 0 and target_cost_per_session > 0
        else 0
    )
    sessions_to_target = max(target_sessions - sessions, 0)
    month_end = current_month.end_time.normalize()
    remaining_days = max(int((month_end - latest_day.normalize()).days), 0)
    pace_per_week = sessions / max((latest_day.day / 7), 1)

    return {
        "month": latest_day.strftime("%b %Y"),
        "sessions": sessions,
        "cost_per_session": cost_per_session,
        "target_sessions": target_sessions,
        "sessions_to_target": sessions_to_target,
        "remaining_days": remaining_days,
        "pace_per_week": pace_per_week,
    }


def calendar_matrix(df: pd.DataFrame) -> pd.DataFrame:
    days = session_days(df)
    if days.empty:
        return pd.DataFrame()

    start = days.min().normalize()
    end = days.max().normalize()
    all_days = pd.date_range(start=start, end=end, freq="D")
    trained = set(days.dt.date)

    calendar = pd.DataFrame({"date": all_days})
    calendar["week"] = calendar["date"].dt.to_period("W-SUN").apply(lambda value: value.start_time.date())
    calendar["day"] = calendar["date"].dt.day_name().str[:3]
    calendar["trained"] = calendar["date"].dt.date.apply(lambda value: "Y" if value in trained else "")

    day_order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    matrix = calendar.pivot(index="week", columns="day", values="trained").fillna("")
    return matrix.reindex(columns=day_order, fill_value="")


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
