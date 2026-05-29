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


def summary_row(lookup: pd.DataFrame, muscle: str) -> pd.Series:
    if muscle in lookup.index:
        return lookup.loc[muscle]
    return pd.Series({"Muscle": muscle, "Days ago": pd.NA, "Target sets, 14d": 0, "Coverage": 0})


def muscle_fill(row: pd.Series) -> str:
    status = muscle_status(row)
    return {
        "covered": "#178f5f",
        "light": "#f1a61b",
        "due": "#e0523f",
        "untouched": "#d1d5db",
    }[status]


def muscle_tooltip(row: pd.Series) -> str:
    muscle = escape(str(row.get("Muscle", "")))
    days = "never" if pd.isna(row["Days ago"]) else f"{int(row['Days ago'])}d ago"
    sets = f"{row['Target sets, 14d']:.1f} weighted sets"
    return f"{muscle}: {sets}, {days}"


def muscle_shape(lookup: pd.DataFrame, muscle: str, shape: str, attrs: str) -> str:
    row = summary_row(lookup, muscle)
    return f"""
        <{shape} {attrs}
            fill="{muscle_fill(row)}"
            stroke="#111827"
            stroke-width="1.2"
            opacity="0.92">
            <title>{muscle_tooltip(row)}</title>
        </{shape}>
    """


def render_body_heatmap(lookup: pd.DataFrame) -> str:
    zones = [
        muscle_shape(lookup, "Traps", "path", 'd="M255 42 L275 42 L286 58 L244 58 Z"'),
        muscle_shape(lookup, "Upper chest", "rect", 'x="78" y="64" width="44" height="15" rx="5"'),
        muscle_shape(lookup, "Chest", "rect", 'x="62" y="79" width="34" height="34" rx="9"'),
        muscle_shape(lookup, "Chest", "rect", 'x="104" y="79" width="34" height="34" rx="9"'),
        muscle_shape(lookup, "Core", "rect", 'x="78" y="118" width="44" height="48" rx="10"'),
        muscle_shape(lookup, "Front delts", "circle", 'cx="48" cy="76" r="14"'),
        muscle_shape(lookup, "Front delts", "circle", 'cx="152" cy="76" r="14"'),
        muscle_shape(lookup, "Side delts", "ellipse", 'cx="37" cy="96" rx="12" ry="22"'),
        muscle_shape(lookup, "Side delts", "ellipse", 'cx="163" cy="96" rx="12" ry="22"'),
        muscle_shape(lookup, "Biceps", "rect", 'x="27" y="118" width="18" height="42" rx="9"'),
        muscle_shape(lookup, "Biceps", "rect", 'x="155" y="118" width="18" height="42" rx="9"'),
        muscle_shape(lookup, "Forearms", "rect", 'x="22" y="164" width="16" height="52" rx="8"'),
        muscle_shape(lookup, "Forearms", "rect", 'x="162" y="164" width="16" height="52" rx="8"'),
        muscle_shape(lookup, "Quads", "rect", 'x="68" y="176" width="25" height="72" rx="10"'),
        muscle_shape(lookup, "Quads", "rect", 'x="107" y="176" width="25" height="72" rx="10"'),
        muscle_shape(lookup, "Calves", "rect", 'x="70" y="254" width="20" height="66" rx="9"'),
        muscle_shape(lookup, "Calves", "rect", 'x="110" y="254" width="20" height="66" rx="9"'),
        muscle_shape(lookup, "Cardio", "circle", 'cx="100" cy="100" r="8"'),
        muscle_shape(lookup, "Rear delts", "circle", 'cx="220" cy="78" r="13"'),
        muscle_shape(lookup, "Rear delts", "circle", 'cx="340" cy="78" r="13"'),
        muscle_shape(lookup, "Upper back", "rect", 'x="245" y="64" width="70" height="45" rx="12"'),
        muscle_shape(lookup, "Lats", "path", 'd="M235 105 Q250 128 258 166 L242 166 Q230 132 220 108 Z"'),
        muscle_shape(lookup, "Lats", "path", 'd="M325 105 Q310 128 302 166 L318 166 Q330 132 340 108 Z"'),
        muscle_shape(lookup, "Triceps", "rect", 'x="206" y="112" width="18" height="48" rx="9"'),
        muscle_shape(lookup, "Triceps", "rect", 'x="336" y="112" width="18" height="48" rx="9"'),
        muscle_shape(lookup, "Glutes", "rect", 'x="250" y="154" width="60" height="34" rx="13"'),
        muscle_shape(lookup, "Hamstrings", "rect", 'x="246" y="195" width="25" height="62" rx="10"'),
        muscle_shape(lookup, "Hamstrings", "rect", 'x="289" y="195" width="25" height="62" rx="10"'),
        muscle_shape(lookup, "Calves", "rect", 'x="248" y="263" width="20" height="58" rx="9"'),
        muscle_shape(lookup, "Calves", "rect", 'x="292" y="263" width="20" height="58" rx="9"'),
    ]

    return f"""
        <section class="body-card">
            <div class="body-title">Body heatmap</div>
            <svg class="body-svg" viewBox="0 0 380 342" role="img" aria-label="Human body muscle heatmap">
                <text x="100" y="24" text-anchor="middle" class="body-label">Front</text>
                <text x="280" y="24" text-anchor="middle" class="body-label">Back</text>
                <circle cx="100" cy="42" r="18" fill="#f3f4f6" stroke="#111827" stroke-width="1.2"/>
                <circle cx="280" cy="42" r="18" fill="#f3f4f6" stroke="#111827" stroke-width="1.2"/>
                <path d="M65 60 Q100 43 135 60 L142 170 Q100 188 58 170 Z" fill="#f8fafc" stroke="#111827" stroke-width="1.2"/>
                <path d="M245 60 Q280 43 315 60 L322 170 Q280 188 238 170 Z" fill="#f8fafc" stroke="#111827" stroke-width="1.2"/>
                {''.join(zones)}
            </svg>
            <div class="body-legend">
                <span><i class="covered"></i>covered</span>
                <span><i class="light"></i>light</span>
                <span><i class="due"></i>due</span>
                <span><i class="untouched"></i>untouched</span>
            </div>
        </section>
    """


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
            .body-card {{
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                background: #ffffff;
                padding: 12px;
                margin: 8px 0 14px;
            }}
            .body-title {{
                color: #111827;
                font-size: 0.95rem;
                font-weight: 700;
                margin-bottom: 6px;
            }}
            .body-svg {{
                display: block;
                height: auto;
                max-width: 620px;
                width: 100%;
            }}
            .body-label {{
                fill: #4b5563;
                font-size: 13px;
                font-weight: 650;
            }}
            .body-legend {{
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
                color: #4b5563;
                font-size: 0.78rem;
                margin-top: 6px;
            }}
            .body-legend span {{
                align-items: center;
                display: inline-flex;
                gap: 5px;
            }}
            .body-legend i {{
                border: 1px solid #111827;
                border-radius: 999px;
                display: inline-block;
                height: 10px;
                width: 10px;
            }}
            .body-legend .covered {{ background: #178f5f; }}
            .body-legend .light {{ background: #f1a61b; }}
            .body-legend .due {{ background: #e0523f; }}
            .body-legend .untouched {{ background: #d1d5db; }}
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
        {render_body_heatmap(lookup)}
        <div class="muscle-board">{''.join(sections)}</div>
    """
    component_height = 520 + 210 * len(MUSCLE_SECTIONS)
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
