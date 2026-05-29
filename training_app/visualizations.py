from __future__ import annotations

from html import escape

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from .analytics import (
    build_muscle_summary,
    build_next_muscle_suggestions,
    canonicalize_muscle_column,
    muscle_status,
)
from .config import MUSCLE_SECTIONS

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
