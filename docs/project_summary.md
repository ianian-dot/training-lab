# Training Lab Project Summary

Training Lab is a personal workout analytics dashboard built with Streamlit and pandas. It turns quick gym logs from CSV files and Google Forms into progress charts, muscle coverage, calculated training load, and practical next-session suggestions.

## What It Does

- Logs gym exercises with sets, reps, entered weight, weight basis, RPE, and notes.
- Reads multiple data sources: seed CSV, frozen legacy Google Form export, and a new live Google Sheet.
- Converts Google Form responses from wide format into long-format exercise rows for analysis.
- Normalises messy exercise names from older `Other exercise` entries, such as inclined bench, hammer curls, and leg press calves.
- Calculates `load_kg` from the entered weight, including 20kg barbell logic for bench and incline bench.
- Maps exercises to weighted target muscles so the dashboard can show what has been trained recently.
- Provides a gym-friendly view for deciding what to train next based on recency and recent target sets.
- Visualises progress over time using load, volume, estimated 1RM, muscle target trends, and a body heatmap.

## Why It Is Useful

The project solves a real personal workflow: logging workouts quickly during a gym session, then using the history to make better decisions next time. Instead of guessing what feels neglected, the app quantifies recent training coverage by muscle group and highlights what looks due.

## What Makes It Special

- It is built around an actual repeated habit, so the product requirements come from real use rather than a toy dataset.
- It bridges messy personal data into structured analytics: Apple Notes, old Google Forms, new Google Forms, and manual CSVs.
- It demonstrates practical data engineering: schema normalisation, wide-to-long transformation, deduplication, and canonical naming.
- It uses domain modelling: exercises are mapped to primary and secondary muscle targets with weighted set counts.
- It is phone-aware: Google Forms handles fast gym-floor logging, while Streamlit provides the dashboard.
- It has a clear growth path into broader health analytics, including pickleball, football, sleep, mood, and recovery.

## Interview Talking Points

- I built a personal analytics app to make my workout tracking more actionable.
- The system ingests data from Google Forms and CSVs, normalises it into a consistent schema, then calculates strength and muscle coverage metrics.
- A key challenge was handling imperfect user-entered data, especially old form entries where new exercises were typed into `Other exercise`.
- I modularised the code into configuration, data processing, analytics, visualisation, and Streamlit view layers so it is easier to maintain and explain.
- The dashboard gives practical recommendations, such as which muscles have not been trained recently and what target to aim for on a repeated lift.
- The project uses Git and GitHub for version control, so each working change is committed, pushed, and recoverable.

## Code Structure

- `app.py`: Streamlit entry point and tab wiring.
- `training_app/config.py`: exercise lists, muscle mappings, file paths, and schema constants.
- `training_app/data.py`: Google Sheet reading, CSV loading, form normalisation, date fallback, and calculated load.
- `training_app/analytics.py`: volume, estimated 1RM, muscle target sets, recency, and next-target calculations.
- `training_app/visualizations.py`: muscle coverage tiles and body heatmap rendering.
- `training_app/views.py`: Streamlit tabs and user-facing screens.

## Pickleball, Football, Sleep, And Mood

Pickleball and football should probably be logged through a separate activity form rather than the lifting form. They share some fields with workouts, such as date, duration, calories, heart rate, RPE, and notes, but they do not have sets, reps, and weights.

The clean long-term design is:

- `strength_sessions`: gym exercises, sets, reps, weights, RPE, muscle mapping.
- `activity_sessions`: pickleball, football, cycling, walking, duration, heart rate, perceived effort, enjoyment.
- `recovery_daily`: sleep duration, deep sleep, sleep quality, morning mood, afternoon mood, stress, energy.

Those tables can later feed one unified dashboard that asks better questions, such as whether poor sleep affects training performance, whether pickleball changes recovery, and which habits correlate with better mood or gym quality.
