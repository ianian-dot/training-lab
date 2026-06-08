from __future__ import annotations

import streamlit as st

from training_app.config import DEFAULT_GOOGLE_SHEET_URL
from training_app.data import load_sports, load_workouts, to_google_sheet_csv_url
from training_app.views import (
    render_dashboard,
    render_data,
    render_gym_view,
    render_log_form,
    render_mappings,
    render_muscle_trends,
    render_progress,
    render_recovery_trends,
    render_setup,
    render_sports,
)


def main() -> None:
    st.set_page_config(page_title="Training Lab", page_icon=":material/fitness_center:", layout="wide")
    st.title("Training Lab")
    st.caption("Log the lifts you actually do, then watch consistency, volume, and strength trends.")

    default_sheet_url = st.secrets.get("google_sheet_url", DEFAULT_GOOGLE_SHEET_URL)

    st.sidebar.header("Data source")
    google_sheet_url = st.sidebar.text_input(
        "New Google Sheet URL",
        value=default_sheet_url,
        placeholder="https://docs.google.com/spreadsheets/d/.../edit?gid=...",
    ).strip()
    csv_url = google_sheet_url or None
    st.sidebar.caption(
        "Using: local seed CSV + legacy form CSV"
        + (" + new Google Sheet" if csv_url else "")
    )
    if csv_url:
        st.sidebar.caption(f"CSV export: {to_google_sheet_csv_url(csv_url)}")

    df = load_workouts(csv_url)
    sports = load_sports()
    (
        gym_tab,
        log_tab,
        progress_tab,
        muscle_trends_tab,
        recovery_trends_tab,
        sports_tab,
        dashboard_tab,
        setup_tab,
        data_tab,
        mappings_tab,
    ) = st.tabs(
        [
            "Gym view",
            "Log workout",
            "Progress",
            "Muscle trends",
            "Recovery trends",
            "Sports",
            "Dashboard",
            "Setup",
            "Data",
            "Mappings",
        ]
    )

    with gym_tab:
        render_gym_view(df)
    with log_tab:
        render_log_form()
    with progress_tab:
        render_progress(df)
    with muscle_trends_tab:
        render_muscle_trends(df)
    with recovery_trends_tab:
        render_recovery_trends(df)
    with sports_tab:
        render_sports(sports)
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
