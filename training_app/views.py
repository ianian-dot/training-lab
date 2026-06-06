from __future__ import annotations

from datetime import date, datetime, time

import pandas as pd
import streamlit as st

from .analytics import (
    build_muscle_summary,
    build_muscle_target_table,
    build_next_muscle_suggestions,
    calendar_matrix,
    cost_summary,
    current_month_summary,
    daily_efficiency,
    daily_recovery_performance,
    exercise_progress_summary,
    format_current_target,
    format_set_target,
    latest_body_metrics,
    monthly_training_summary,
    protein_performance_summary,
    rest_day_summary,
    session_days,
    weekly_session_counts,
)
from .config import (
    EXERCISES,
    EXERCISE_CATEGORIES,
    FORM_SCRIPT_PATH,
    LEGACY_FORM_PATH,
    MUSCLE_GROUPS,
    MUSCLE_SECTIONS,
    MUSCLE_TARGETS,
    PER_SIDE_BASE_LOAD_KG,
    SPORTS_BODY_PART_TARGETS,
    SPORTS_FORM_SCRIPT_PATH,
    WORKOUTS_PATH,
)
from .data import append_workout, canonical_label
from .visualizations import format_days_ago, render_muscle_target_visual


def render_recovery_trends(df: pd.DataFrame) -> None:
    st.subheader("Recovery trends")

    daily = daily_recovery_performance(df)
    if daily.empty:
        st.info("Log workouts with recovery details to unlock these charts.")
        return

    st.caption("These charts are exploratory. They show relationships, not proof that protein caused a change.")

    weight_col, protein_col = st.columns(2)
    with weight_col:
        st.markdown("**Body weight over time**")
        weight = daily.dropna(subset=["body_weight_kg"])
        if weight.empty:
            st.info("No body weight entries yet.")
        else:
            st.line_chart(weight, x="day", y="body_weight_kg", use_container_width=True)

    with protein_col:
        st.markdown("**Protein and workout volume**")
        protein_volume = daily[["day", "protein_grams", "volume_kg"]].copy()
        if protein_volume[["protein_grams", "volume_kg"]].dropna(how="all").empty:
            st.info("No protein or volume entries yet.")
        else:
            st.line_chart(protein_volume, x="day", y=["protein_grams", "volume_kg"], use_container_width=True)

    st.markdown("**Performance and session quality over time**")
    trend_options = {
        "Volume": "volume_kg",
        "Best load": "load_kg",
        "Estimated 1RM": "estimated_1rm_kg",
        "Session quality": "session_quality",
        "Energy": "energy",
        "Motivation": "motivation",
        "Sleep": "sleep_hours",
        "Avg heart rate": "avg_heart_rate",
    }
    selected = st.multiselect(
        "Metrics",
        list(trend_options),
        default=["Volume", "Session quality", "Energy"],
    )
    trend_columns = [trend_options[label] for label in selected]
    if trend_columns:
        st.line_chart(daily[["day", *trend_columns]], x="day", y=trend_columns, use_container_width=True)
    else:
        st.info("Choose at least one metric.")

    compare_col, table_col = st.columns([1, 1])
    with compare_col:
        st.markdown("**Protein logged vs not logged**")
        comparison = protein_performance_summary(df)
        if comparison.empty or len(comparison) < 2:
            st.info("Log a few days with and without protein to make this comparison useful.")
        else:
            st.dataframe(
                comparison.round(
                    {
                        "avg_volume_kg": 0,
                        "avg_session_quality": 1,
                        "avg_energy": 1,
                        "avg_body_weight_kg": 1,
                    }
                ),
                hide_index=True,
                use_container_width=True,
            )

    with table_col:
        st.markdown("**Daily recovery summary**")
        summary = daily[
            [
                "day",
                "body_weight_kg",
                "protein_grams",
                "volume_kg",
                "session_quality",
                "energy",
                "sleep_hours",
            ]
        ].copy()
        summary["day"] = summary["day"].dt.strftime("%Y-%m-%d")
        st.dataframe(summary.round(1), hide_index=True, use_container_width=True)


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

        session_type = left.selectbox("Session", ["Upper", "Push", "Pull", "Legs", "Arms", "Full body", "Cardio", "Other"])
        exercise_category = right.selectbox("Exercise group", [*EXERCISE_CATEGORIES, "All", "Custom"])

        if exercise_category == "Custom":
            exercise_choice = "Custom"
        else:
            exercise_options = (
                sorted(EXERCISES)
                if exercise_category == "All"
                else EXERCISE_CATEGORIES[exercise_category]
            )
            exercise_choice = right.selectbox("Exercise", exercise_options)

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
    snapshot = exercise_progress_summary(df)
    if not snapshot.empty:
        st.markdown("**All exercise snapshot**")
        display = snapshot.copy()
        display["Last done"] = display["Last done"].dt.strftime("%Y-%m-%d")
        st.dataframe(
            display.round(
                {
                    "Latest load": 1,
                    "Previous load": 1,
                    "Load change": 1,
                    "Best load": 1,
                    "Latest est. 1RM": 1,
                    "Best est. 1RM": 1,
                    "Latest volume": 0,
                }
            ),
            hide_index=True,
            use_container_width=True,
        )
        st.caption("Load change compares the latest logged row for that exercise with the previous logged row.")

    st.divider()
    exercise_options = sorted(df["exercise"].dropna().unique())
    selected = st.selectbox("Exercise", exercise_options, key="progress_exercise")
    metric_label = st.segmented_control(
        "Metric",
        ["Load", "Entered weight", "Volume", "Estimated 1RM", "Reps"],
        default="Load",
    )

    metric_map = {
        "Load": "load_kg",
        "Entered weight": "weight_kg",
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
                load_kg=("load_kg", "max"),
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
                "load_kg",
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
    days = session_days(df)
    rest = rest_day_summary(df)

    st.markdown("**Overall training dashboard**")
    monthly_fee = st.number_input(
        "Monthly gym cost",
        min_value=0.0,
        max_value=1000.0,
        value=110.0,
        step=5.0,
        help="Used only for cost-per-session estimates.",
    )
    target_cost = st.number_input(
        "Target cost per session",
        min_value=1.0,
        max_value=100.0,
        value=10.0,
        step=1.0,
        help="Used to calculate how many gym sessions make your monthly membership feel efficient.",
    )
    cost = cost_summary(df, monthly_fee)
    month = current_month_summary(df, monthly_fee, target_cost)

    st.markdown(f"**This month: {month['month']}**")
    month_cols = st.columns(5)
    month_cols[0].metric("Sessions this month", int(month["sessions"]))
    month_cost = month["cost_per_session"]
    month_cols[1].metric("Current cost / session", "-" if month_cost is None else f"${month_cost:.2f}")
    month_cols[2].metric("Target sessions", int(month["target_sessions"]), f"for ${target_cost:.0f}/session")
    month_cols[3].metric("More to target", int(month["sessions_to_target"]))
    month_cols[4].metric("Days left in month", int(month["remaining_days"]))

    if month["sessions_to_target"]:
        st.info(
            f"{int(month['sessions_to_target'])} more gym session(s) this month would bring the membership "
            f"to about ${target_cost:.0f} per session."
        )
    else:
        st.success("You have already hit your target cost efficiency for this month.")

    st.markdown("**Latest body and session context**")
    latest_metrics = latest_body_metrics(df)

    def metric_label(field: str, suffix: str = "", precision: int = 1) -> str:
        value = latest_metrics[field]["value"]
        if pd.isna(value) or value is None:
            return "-"
        if isinstance(value, (int, float)):
            return f"{value:.{precision}f}{suffix}"
        return f"{value}{suffix}"

    body_cols = st.columns(5)
    weight_date = latest_metrics["body_weight_kg"]["date"]
    weight_delta = "-" if pd.isna(weight_date) or weight_date is None else pd.to_datetime(weight_date).strftime("%b %d")
    body_cols[0].metric("Latest weight", metric_label("body_weight_kg", " kg"), weight_delta)
    body_cols[1].metric("Latest protein", metric_label("protein_grams", " g", precision=0))
    body_cols[2].metric("Latest calories", metric_label("calories", " kcal", precision=0))
    body_cols[3].metric("Latest duration", metric_label("duration_min", " min", precision=0))
    body_cols[4].metric("Latest avg HR", metric_label("avg_heart_rate", " bpm", precision=0))

    context_cols = st.columns(5)
    context_cols[0].metric("Max HR", metric_label("max_heart_rate", " bpm", precision=0))
    context_cols[1].metric("Energy", metric_label("energy", "/10", precision=0))
    context_cols[2].metric("Motivation", metric_label("motivation", "/10", precision=0))
    context_cols[3].metric("Session quality", metric_label("session_quality", "/10", precision=0))
    context_cols[4].metric("Sleep", metric_label("sleep_hours", " h"))

    first_day = days.min().strftime("%b %d, %Y") if not days.empty else "-"
    latest_session = days.max().strftime("%b %d, %Y") if not days.empty else "-"
    weekly_counts = weekly_session_counts(df)
    avg_sessions_week = weekly_counts["sessions"].mean() if not weekly_counts.empty else 0

    overview_cols = st.columns(5)
    overview_cols[0].metric("Sessions", int(rest["sessions"]), f"since {first_day}")
    overview_cols[1].metric("Latest session", latest_session)
    overview_cols[2].metric("Avg / week", f"{avg_sessions_week:.1f}")
    avg_rest = rest["avg_rest_days"]
    overview_cols[3].metric("Avg rest days", "-" if avg_rest is None else f"{avg_rest:.1f}")
    cost_per_session = cost["cost_per_session"]
    overview_cols[4].metric("Cost / session", "-" if cost_per_session is None else f"${cost_per_session:.2f}")

    detail_cols = st.columns(3)
    detail_cols[0].metric("Covered months", int(cost["months"]))
    detail_cols[1].metric("Est. total gym cost", f"${cost['total_cost']:.0f}")
    longest_rest = rest["longest_rest_days"]
    detail_cols[2].metric("Longest rest", "-" if longest_rest is None else f"{longest_rest} days")

    st.markdown("**Efficiency**")
    efficiency = daily_efficiency(df)
    latest_efficiency = efficiency.dropna(subset=["duration_min"]).iloc[-1] if not efficiency.empty else None
    efficiency_cols = st.columns(4)
    if latest_efficiency is None:
        efficiency_cols[0].metric("Latest volume / min", "-")
        efficiency_cols[1].metric("Latest sets / min", "-")
        efficiency_cols[2].metric("Latest exercises / hour", "-")
        efficiency_cols[3].metric("Tracked duration", "-")
    else:
        efficiency_cols[0].metric("Latest volume / min", f"{latest_efficiency['volume_per_min']:.1f} kg")
        efficiency_cols[1].metric("Latest sets / min", f"{latest_efficiency['sets_per_min']:.2f}")
        efficiency_cols[2].metric("Latest exercises / hour", f"{latest_efficiency['exercises_per_hour']:.1f}")
        efficiency_cols[3].metric("Tracked duration", f"{latest_efficiency['duration_min']:.0f} min")

    if not efficiency.empty and not efficiency[["volume_per_min", "sets_per_min"]].dropna(how="all").empty:
        st.line_chart(
            efficiency[["day", "volume_per_min", "sets_per_min"]],
            x="day",
            y=["volume_per_min", "sets_per_min"],
            use_container_width=True,
        )
        st.caption("Efficiency depends heavily on logging duration consistently. It is most useful within similar session types.")

    monthly = monthly_training_summary(df)
    if not monthly.empty:
        st.markdown("**Month over month**")
        latest_month = monthly.iloc[-1]
        previous_month = monthly.iloc[-2] if len(monthly) > 1 else None
        month_cols = st.columns(4)
        session_delta = None if previous_month is None else int(latest_month["sessions"] - previous_month["sessions"])
        volume_delta = None if previous_month is None else latest_month["total_volume_kg"] - previous_month["total_volume_kg"]
        sets_delta = None if previous_month is None else latest_month["total_sets"] - previous_month["total_sets"]
        efficiency_delta = (
            None
            if previous_month is None
            else latest_month.get("avg_volume_per_min", 0) - previous_month.get("avg_volume_per_min", 0)
        )
        month_cols[0].metric("Sessions", int(latest_month["sessions"]), session_delta)
        month_cols[1].metric("Volume", f"{latest_month['total_volume_kg']:,.0f} kg", None if volume_delta is None else f"{volume_delta:,.0f}")
        month_cols[2].metric("Sets", f"{latest_month['total_sets']:.0f}", None if sets_delta is None else f"{sets_delta:.0f}")
        avg_eff = latest_month.get("avg_volume_per_min")
        month_cols[3].metric(
            "Avg volume / min",
            "-" if pd.isna(avg_eff) else f"{avg_eff:.1f} kg",
            None if efficiency_delta is None or pd.isna(efficiency_delta) else f"{efficiency_delta:.1f}",
        )

        monthly_table = monthly.copy()
        monthly_table["month"] = monthly_table["month"].dt.strftime("%Y-%m")
        st.dataframe(
            monthly_table[
                [
                    "month",
                    "sessions",
                    "total_sets",
                    "total_volume_kg",
                    "avg_duration_min",
                    "avg_volume_per_min",
                    "avg_session_quality",
                ]
            ].round(1),
            hide_index=True,
            use_container_width=True,
        )

    trend_col, calendar_col = st.columns([1, 1.2])
    with trend_col:
        st.markdown("**Gym sessions per week**")
        if weekly_counts.empty:
            st.info("Log a session to see weekly frequency.")
        else:
            st.bar_chart(weekly_counts, x="week_start", y="sessions", use_container_width=True)

    with calendar_col:
        st.markdown("**Training calendar**")
        calendar = calendar_matrix(df)
        if calendar.empty:
            st.info("Log a session to see the calendar.")
        else:
            st.dataframe(calendar, use_container_width=True)
            st.caption("Y = at least one gym session that day.")

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
        st.line_chart(exercise_df, x="date", y=["load_kg", "estimated_1rm_kg"], use_container_width=True)
        st.caption("Estimated 1RM uses calculated load x (1 + reps / 30).")

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
                "time_validation",
                "session_type",
                "exercise",
                "muscle_group",
                "sets",
                "reps",
                "weight_kg",
                "weight_basis",
                "load_kg",
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
    st.write("Open the script below in Google Apps Script, run `createTrainingLabForm`, and it will create a fresh Google Form plus linked response sheet.")
    st.code(str(FORM_SCRIPT_PATH), language="text")

    st.markdown("**Create the sports form**")
    st.write("Use a separate form for pickleball and football so those sessions do not get mixed into lift sets/reps/load.")
    st.code(str(SPORTS_FORM_SCRIPT_PATH), language="text")

    st.markdown("**Connect the sheet**")
    st.write("After responses start coming in, share the new response sheet as viewable by anyone with the link, then paste that new sheet URL into the sidebar.")
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
    if LEGACY_FORM_PATH.exists():
        st.caption(f"Legacy Google Form snapshot: {LEGACY_FORM_PATH}")

    export = df.copy()
    if not export.empty:
        export["date"] = export["date"].dt.strftime("%Y-%m-%d")
    st.dataframe(export, hide_index=True, use_container_width=True)

    if "time_validation" in df.columns:
        time_checks = df[df["time_validation"].fillna("").astype(str).str.strip() != ""].copy()
        if not time_checks.empty:
            st.markdown("**Start time validation**")
            display = time_checks[["date", "start_time", "time_validation", "exercise", "notes"]].copy()
            display["date"] = display["date"].dt.strftime("%Y-%m-%d")
            st.dataframe(display, hide_index=True, use_container_width=True)

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

    st.markdown("**Per-side base load assumptions**")
    if PER_SIDE_BASE_LOAD_KG:
        assumptions = pd.DataFrame(
            [
                {
                    "Exercise": exercise,
                    "Base load added when weight basis is per side": f"{base_load:g} kg",
                    "Formula": f"{base_load:g} + entered weight x 2",
                }
                for exercise, base_load in sorted(PER_SIDE_BASE_LOAD_KG.items())
            ]
        )
        st.dataframe(assumptions, hide_index=True, use_container_width=True)
        st.caption("Configure these defaults in training_app/config.py under PER_SIDE_BASE_LOAD_KG.")
    else:
        st.info("No per-side base load assumptions are configured.")

    st.markdown("**Raw mapping weights**")
    raw_rows = []
    for exercise, targets in sorted(MUSCLE_TARGETS.items()):
        for muscle, weight in targets.items():
            raw_rows.append({"Exercise": exercise, "Muscle": muscle, "Weight": weight})
    st.dataframe(pd.DataFrame(raw_rows), hide_index=True, use_container_width=True)

    st.markdown("**Sports body-part mapping**")
    sports_rows = []
    for sport, targets in SPORTS_BODY_PART_TARGETS.items():
        for body_part, emphasis in targets.items():
            sports_rows.append({"Sport": sport, "Body part": body_part, "Emphasis": emphasis})
    st.dataframe(pd.DataFrame(sports_rows), hide_index=True, use_container_width=True)
