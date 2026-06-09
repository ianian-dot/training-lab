from __future__ import annotations

import pandas as pd

from .config import ALL_TRACKED_MUSCLES, MUSCLE_TARGETS


WEEKDAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
TIME_BUCKET_ORDER = ["Morning", "Afternoon", "Evening", "Night", "Unknown"]


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


def latest_value(df: pd.DataFrame, column: str) -> dict[str, object]:
    if column not in df.columns:
        return {"value": None, "date": None}

    values = df.dropna(subset=["date", column]).copy()
    if values.empty:
        return {"value": None, "date": None}

    latest = values.sort_values("date").iloc[-1]
    return {"value": latest[column], "date": latest["date"]}


def latest_body_metrics(df: pd.DataFrame) -> dict[str, dict[str, object]]:
    fields = [
        "body_weight_kg",
        "protein_grams",
        "calories",
        "duration_min",
        "avg_heart_rate",
        "max_heart_rate",
        "energy",
        "motivation",
        "session_quality",
        "sleep_hours",
    ]
    return {field: latest_value(df, field) for field in fields}


def daily_recovery_performance(df: pd.DataFrame) -> pd.DataFrame:
    workouts = workout_rows(df).dropna(subset=["date"]).copy()
    if workouts.empty:
        return pd.DataFrame()

    workouts["day"] = pd.to_datetime(workouts["date"]).dt.normalize()
    daily = (
        workouts.groupby("day", as_index=False)
        .agg(
            body_weight_kg=("body_weight_kg", "max"),
            protein_grams=("protein_grams", "max"),
            calories=("calories", "max"),
            duration_min=("duration_min", "max"),
            avg_heart_rate=("avg_heart_rate", "max"),
            volume_kg=("volume_kg", "sum"),
            load_kg=("load_kg", "max"),
            estimated_1rm_kg=("estimated_1rm_kg", "max"),
            rpe=("rpe", "mean"),
            energy=("energy", "max"),
            motivation=("motivation", "max"),
            session_quality=("session_quality", "max"),
            sleep_hours=("sleep_hours", "max"),
        )
        .sort_values("day")
    )
    daily["protein_logged"] = daily["protein_grams"].fillna(0) > 0
    daily["performance_score"] = daily["volume_kg"].fillna(0)
    return daily


def protein_performance_summary(df: pd.DataFrame) -> pd.DataFrame:
    daily = daily_recovery_performance(df)
    if daily.empty:
        return pd.DataFrame()

    summary = (
        daily.groupby("protein_logged", as_index=False)
        .agg(
            days=("day", "count"),
            avg_volume_kg=("volume_kg", "mean"),
            avg_session_quality=("session_quality", "mean"),
            avg_energy=("energy", "mean"),
            avg_body_weight_kg=("body_weight_kg", "mean"),
        )
        .replace({"protein_logged": {True: "Protein logged", False: "No protein logged"}})
    )
    return summary


def daily_efficiency(df: pd.DataFrame) -> pd.DataFrame:
    workouts = workout_rows(df).dropna(subset=["date"]).copy()
    if workouts.empty:
        return pd.DataFrame()

    workouts["day"] = pd.to_datetime(workouts["date"]).dt.normalize()
    daily = (
        workouts.groupby("day", as_index=False)
        .agg(
            duration_min=("duration_min", "max"),
            total_sets=("sets", "sum"),
            total_reps=("reps", "sum"),
            volume_kg=("volume_kg", "sum"),
            exercise_count=("exercise", "nunique"),
            avg_rpe=("rpe", "mean"),
            session_quality=("session_quality", "max"),
        )
        .sort_values("day")
    )

    usable_duration = daily["duration_min"].where(daily["duration_min"] > 0)
    daily["volume_per_min"] = daily["volume_kg"] / usable_duration
    daily["sets_per_min"] = daily["total_sets"] / usable_duration
    daily["exercises_per_hour"] = daily["exercise_count"] / usable_duration * 60
    return daily


def _first_filled(values: pd.Series) -> object:
    filled = values.dropna()
    filled = filled[filled.astype(str).str.strip() != ""]
    return None if filled.empty else filled.iloc[0]


def _parse_start_hour(value: object) -> float | None:
    if pd.isna(value) or str(value).strip() == "":
        return None
    parsed = pd.to_datetime(str(value), errors="coerce")
    if pd.isna(parsed):
        return None
    return float(parsed.hour + parsed.minute / 60)


def _time_of_day(hour: float | None) -> str:
    if hour is None or pd.isna(hour):
        return "Unknown"
    if 8 <= hour < 12:
        return "Morning"
    if 12 <= hour < 17:
        return "Afternoon"
    if 17 <= hour < 21:
        return "Evening"
    if 21 <= hour < 24:
        return "Night"
    return "Unknown"


def daily_session_insights(df: pd.DataFrame) -> pd.DataFrame:
    workouts = workout_rows(df).dropna(subset=["date"]).copy()
    if workouts.empty:
        return pd.DataFrame()

    workouts["day"] = pd.to_datetime(workouts["date"]).dt.normalize()
    daily = (
        workouts.groupby("day", as_index=False)
        .agg(
            start_time=("start_time", _first_filled),
            calories=("calories", "max"),
            duration_min=("duration_min", "max"),
            total_sets=("sets", "sum"),
            total_volume_kg=("volume_kg", "sum"),
            exercise_count=("exercise", "nunique"),
            avg_rpe=("rpe", "mean"),
            energy=("energy", "max"),
            motivation=("motivation", "max"),
            session_quality=("session_quality", "max"),
        )
        .sort_values("day")
    )

    usable_duration = daily["duration_min"].where(daily["duration_min"] > 0)
    daily["volume_per_min"] = daily["total_volume_kg"] / usable_duration
    daily["sets_per_min"] = daily["total_sets"] / usable_duration
    daily["exercises_per_hour"] = daily["exercise_count"] / usable_duration * 60
    daily["productivity_score"] = daily[["energy", "motivation", "session_quality"]].mean(axis=1)
    daily["weekday"] = daily["day"].dt.day_name()
    daily["weekday_order"] = daily["weekday"].map({day: index for index, day in enumerate(WEEKDAY_ORDER)})
    daily["start_hour"] = daily["start_time"].apply(_parse_start_hour)
    daily["time_of_day"] = daily["start_hour"].apply(_time_of_day)
    daily["time_bucket_order"] = daily["time_of_day"].map(
        {bucket: index for index, bucket in enumerate(TIME_BUCKET_ORDER)}
    )
    return daily


def _summarize_sessions(daily: pd.DataFrame, group_column: str, order_column: str) -> pd.DataFrame:
    if daily.empty:
        return pd.DataFrame()

    summary = (
        daily.groupby([group_column, order_column], dropna=False, as_index=False)
        .agg(
            sessions=("day", "count"),
            avg_calories=("calories", "mean"),
            avg_productivity=("productivity_score", "mean"),
            avg_session_quality=("session_quality", "mean"),
            avg_energy=("energy", "mean"),
            avg_motivation=("motivation", "mean"),
            avg_volume_kg=("total_volume_kg", "mean"),
            avg_duration_min=("duration_min", "mean"),
            avg_volume_per_min=("volume_per_min", "mean"),
            avg_sets_per_min=("sets_per_min", "mean"),
            avg_exercise_count=("exercise_count", "mean"),
        )
        .sort_values(order_column)
    )
    return summary.drop(columns=[order_column])


def weekday_session_summary(df: pd.DataFrame) -> pd.DataFrame:
    return _summarize_sessions(daily_session_insights(df), "weekday", "weekday_order")


def time_of_day_session_summary(df: pd.DataFrame) -> pd.DataFrame:
    return _summarize_sessions(daily_session_insights(df), "time_of_day", "time_bucket_order")


def exercise_frequency_summary(df: pd.DataFrame) -> pd.DataFrame:
    workouts = workout_rows(df).dropna(subset=["date", "exercise"]).copy()
    if workouts.empty:
        return pd.DataFrame()

    workouts["day"] = pd.to_datetime(workouts["date"]).dt.normalize()
    summary = (
        workouts.groupby("exercise", as_index=False)
        .agg(
            entries=("exercise", "count"),
            sessions=("day", "nunique"),
            last_done=("date", "max"),
            avg_rpe=("rpe", "mean"),
            avg_load_kg=("load_kg", "mean"),
            best_load_kg=("load_kg", "max"),
            total_volume_kg=("volume_kg", "sum"),
        )
        .sort_values(["sessions", "entries", "last_done"], ascending=[False, False, False])
    )
    return summary


def monthly_training_summary(df: pd.DataFrame) -> pd.DataFrame:
    workouts = workout_rows(df).dropna(subset=["date"]).copy()
    if workouts.empty:
        return pd.DataFrame()

    workouts["month"] = pd.to_datetime(workouts["date"]).dt.to_period("M").dt.to_timestamp()
    sessions = (
        workouts[["month", "date"]]
        .drop_duplicates()
        .groupby("month", as_index=False)
        .agg(sessions=("date", "count"))
    )
    monthly = (
        workouts.groupby("month", as_index=False)
        .agg(
            total_sets=("sets", "sum"),
            total_volume_kg=("volume_kg", "sum"),
            avg_rpe=("rpe", "mean"),
            avg_session_quality=("session_quality", "mean"),
            avg_duration_min=("duration_min", "mean"),
        )
        .merge(sessions, on="month", how="left")
        .sort_values("month")
    )

    efficiency = daily_efficiency(df)
    if not efficiency.empty:
        efficiency["month"] = efficiency["day"].dt.to_period("M").dt.to_timestamp()
        monthly_efficiency = (
            efficiency.groupby("month", as_index=False)
            .agg(avg_volume_per_min=("volume_per_min", "mean"), avg_sets_per_min=("sets_per_min", "mean"))
        )
        monthly = monthly.merge(monthly_efficiency, on="month", how="left")

    for column in ["sessions", "total_sets", "total_volume_kg", "avg_volume_per_min"]:
        monthly[f"{column}_change"] = monthly[column].diff()
    return monthly


def exercise_progress_summary(df: pd.DataFrame) -> pd.DataFrame:
    workouts = workout_rows(df).dropna(subset=["date"]).sort_values("date").copy()
    if workouts.empty:
        return pd.DataFrame()

    rows = []
    for exercise, exercise_df in workouts.groupby("exercise"):
        exercise_df = exercise_df.sort_values("date")
        latest = exercise_df.iloc[-1]
        previous = exercise_df.iloc[-2] if len(exercise_df) > 1 else None
        best_load = exercise_df["load_kg"].max()
        best_1rm = exercise_df["estimated_1rm_kg"].max()

        rows.append(
            {
                "Exercise": exercise,
                "Entries": len(exercise_df),
                "Last done": latest["date"],
                "Latest load": latest["load_kg"],
                "Previous load": None if previous is None else previous["load_kg"],
                "Load change": None if previous is None else latest["load_kg"] - previous["load_kg"],
                "Best load": best_load,
                "Latest est. 1RM": latest["estimated_1rm_kg"],
                "Best est. 1RM": best_1rm,
                "Latest volume": latest["volume_kg"],
            }
        )

    return pd.DataFrame(rows).sort_values(["Last done", "Exercise"], ascending=[False, True])


def _next_weight_increment(weight: float, basis: str) -> float:
    if basis in {"per side", "per hand"}:
        return 1.0 if weight < 10 else 2.5
    if basis == "bodyweight":
        return 0.0
    return 2.5 if weight < 40 else 5.0


def _format_weight_suggestion(weight: float, basis: str) -> str:
    if pd.isna(weight):
        return "Try a small increase next time"
    if basis == "bodyweight":
        return "Try added weight or a harder variation"
    suffix = f" {basis}" if basis else ""
    return f"Try {weight:.1f} kg{suffix}"


def low_rpe_progression_suggestions(
    df: pd.DataFrame,
    recent_entries: int = 3,
    max_average_rpe: float = 6.0,
) -> pd.DataFrame:
    workouts = workout_rows(df).dropna(subset=["date", "exercise", "rpe"]).copy()
    if workouts.empty:
        return pd.DataFrame()

    rows = []
    for exercise, exercise_df in workouts.groupby("exercise"):
        recent = exercise_df.sort_values("date").tail(recent_entries)
        if len(recent) < recent_entries:
            continue

        average_rpe = recent["rpe"].mean()
        if pd.isna(average_rpe) or average_rpe > max_average_rpe:
            continue

        latest = recent.iloc[-1]
        basis = str(latest.get("weight_basis", "") or "").strip()
        current_weight = pd.to_numeric(latest.get("weight_kg"), errors="coerce")
        suggested_weight = current_weight + _next_weight_increment(current_weight, basis)

        rows.append(
            {
                "Exercise": exercise,
                "Last done": latest["date"],
                "Recent avg RPE": average_rpe,
                "Recent RPEs": ", ".join(f"{value:.0f}" for value in recent["rpe"].dropna()),
                "Current logged weight": current_weight,
                "Weight basis": basis or "-",
                "Suggested logged weight": None if pd.isna(suggested_weight) else suggested_weight,
                "Suggestion": _format_weight_suggestion(suggested_weight, basis),
            }
        )

    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values(["Recent avg RPE", "Last done"], ascending=[True, False])


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
