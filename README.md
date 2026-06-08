# Training Lab

[View the app on streamlit](https://ianian-dot-training-lab-app-yl6nrp.streamlit.app)

A personal Streamlit dashboard for logging gym sessions and tracking strength, volume, and consistency.

## Run

```bash
python3 -m streamlit run app.py
```

## Starting exercise list

- Bench press
- Seated lateral raise machine
- Barbell bicep curl
- Dumbbell bicep curl
- Hammer curl
- Single-arm shoulder raise
- Seated shoulder press
- Lat pulldown
- Seated row
- Tricep pulldown
- Overhead dumbbell tricep extension
- Pull-up
- Rear delt machine
- Leg extension
- Incline bench press
- Incline dumbbell press
- Flat dumbbell press
- Pectoral fly
- Reverse pec deck
- Incline T-bar row
- Leg press
- Leg press calf raise
- Cycling
- Stationary bike

Seed workout data is stored in `data/workouts.csv`. The old Google Form responses are snapshotted in `data/legacy_google_form.csv`, and the app reads that file automatically.

The current live Google Form response sheet is configured outside Git using either Streamlit secrets or an environment variable.

## Google Form logging

The gym-friendly workflow is:

1. Submit one Google Form response per gym session.
2. Fill up to 6 exercise blocks as you finish each exercise.
3. If you do more than 6 exercises, submit a second response for the same date and fill only the extra exercise blocks.
4. The form writes to a linked Google Sheet.
5. Paste the new sheet URL into the dashboard sidebar.
6. The dashboard combines the seed CSV, legacy form CSV, and new Google Sheet.

The app does not physically append Google Sheet rows into the CSV during normal use. Instead, every refresh reads each source, normalises them into the same schema, combines them in memory, and deduplicates obvious repeats. This keeps the old records preserved separately while letting the new form become the live source from now on.

The form records start time with 24-hour dropdowns. During import, any old 12-hour entries that look like middle-of-the-night gym sessions are shifted into daytime/evening time.

The app keeps a `time_validation` note when it changes or flags a start time. For example, `3:30 AM` is interpreted as `15:30`, while ambiguous `8:00 AM` to `11:00 AM` entries are kept as morning but shown in the Data tab for review. Going forward, use 24-hour time in the form.

To create the form, use `google_form_creator.gs` in Google Apps Script. Detailed steps are in `docs/google_form_setup.md`.

For pickleball and football, use `sports_form_creator.gs` to create a separate sports form. Sports sessions are tracked separately because they are session-based activities rather than strength rows with sets, reps, and load. The local starter file is `data/sports.csv`.

The Google Sheet stores each session as one wide row, with columns like `Exercise 1`, `Sets 1`, `Exercise 2`, `Sets 2`, and so on. The dashboard converts those exercise blocks into one long-format analysis row per exercise.

The form dropdown is grouped with prefixes such as `Push / Bench press`, `Pull / Lat pulldown`, `Legs / Leg press`, and `Cardio / Stationary bike`. The dashboard strips the prefix and stores the clean exercise name.

The legacy form file is converted the same way. Older `Other exercise` entries are keyword-detected, including inclined bench, hammer curls, leg press calf raises, and stationary bike.

You can also submit a later update with no exercises, for example body weight or protein later in the day. The dashboard stores that as a zero-set `Session update` row so recovery data is kept without changing muscle-volume charts.

If `Weight basis` is blank, the app uses an exercise-specific default such as `per side` for bench press, `per hand` for dumbbell presses/curls, and `total` for most machines. If sets or reps are blank, the app uses that exercise's historical mean when enough past data exists. These inferred values are marked in `imputation_notes`.

For Streamlit to read the sheet, share it as `Anyone with the link can view` or publish it to the web.

For local Streamlit, create `.streamlit/secrets.toml`:

```toml
google_sheet_url = "https://docs.google.com/spreadsheets/d/..."
```

For Streamlit Community Cloud, add the same value as a secret named `google_sheet_url`. You can also set an environment variable named `TRAINING_LAB_GOOGLE_SHEET_URL`.

## Muscle target logic

The app maps each exercise to weighted target muscles. For example:

- Bench press: chest, front delts, triceps
- Incline bench press: upper chest, chest, front delts, triceps
- Incline dumbbell press: upper chest, chest, front delts, triceps
- Flat dumbbell press: chest, front delts, triceps
- Pectoral fly: chest, upper chest, front delts
- Lat pulldown and pull-up: lats, upper back, biceps
- Seated row: upper back, lats, rear delts, biceps
- Lateral raises: side delts
- Shoulder press: front delts, side delts, triceps
- Bicep curls: biceps and forearms
- Hammer curls: brachialis, biceps, forearms
- Tricep pulldown and overhead tricep extension: triceps
- Rear delt machine: rear delts, upper back, traps
- Reverse pec deck: rear delts, upper back, traps
- Leg extension: quads
- Leg press: quads, glutes, hamstrings, calves
- Leg press calf raise: calves
- Incline T-bar row: upper back, lats, rear delts, biceps, traps
- Cycling: cardio, quads, glutes, calves, hamstrings
- Stationary bike: cardio, quads, glutes, calves, hamstrings

The dashboard uses this to estimate target sets per muscle over the last 14 days and suggest what looks most due.

## Sports Mapping

The sports form is designed for pickleball and football. Instead of load and estimated 1RM, it records only the practical basics: duration, active calories, intensity, average/max heart rate, and notes.

The Sports tab currently reads `data/sports.csv`. Backfilled entries can use estimated calories; for example, unknown pickleball sessions are currently set to 450 kcal as a midpoint of the 400-500 kcal active range.

Default body-part mappings:

- Pickleball: calves, quads, glutes, hamstrings, shoulders, forearms, core, cardio
- Football: calves, quads, hamstrings, glutes, hip flexors, core, cardio

These mappings live in `training_app/config.py` under `SPORTS_BODY_PART_TARGETS`.

## Overall Dashboard

The Dashboard tab includes higher-level training consistency metrics:

- total gym sessions since the first logged workout
- workouts this month
- current monthly cost per session
- how many more sessions are needed to hit a target cost per session
- latest body weight, protein, calories, duration, heart rate, sleep, and session ratings
- latest gym session date
- average gym sessions per week
- average and longest rest days between sessions
- Monday-to-Sunday training calendar
- weekly gym session bar chart
- estimated gym cost per session using your monthly fee
- gym efficiency metrics such as volume per minute and sets per minute
- month-over-month comparisons for sessions, volume, sets, and average efficiency

## Recovery Trends

The Recovery trends tab explores how recovery/context data moves alongside training:

- body weight over time
- protein grams over time
- workout volume and performance over time
- session quality, energy, motivation, sleep, and heart rate trends
- simple comparison of days with protein logged versus no protein logged

These charts are exploratory rather than causal. They help generate questions like whether higher-protein days tend to coincide with higher volume or better session quality.

## Weight And Load Logic

`weight_kg` is the number you entered. `load_kg` is the calculated training load used for volume and estimated 1RM.

- `total`: load is the entered weight
- `per hand`: load is entered weight x 2
- `per side`: if the exercise has a configured base load, load is base load + entered weight x 2
- `per side`: if no base load is configured, load is entered weight x 2
- `bodyweight`: load is the entered weight, usually 0 unless you choose to track added weight

Default weight basis assumptions live in `training_app/config.py` under `DEFAULT_WEIGHT_BASIS_BY_EXERCISE`.

Configured `per side` base loads live in `training_app/config.py` under `PER_SIDE_BASE_LOAD_KG`. Current defaults:

- Bench press: 20kg bar
- Incline bench press: 20kg bar
- Leg press: 47kg sled
- Leg press calf raise: 47kg sled

This is deliberately easy to change if your gym machine uses a different starting weight.

## Code Structure

- `app.py`: small Streamlit entry point and tab wiring
- `training_app/config.py`: exercises, muscle mappings, file paths, and schema constants
- `training_app/data.py`: CSV/Google Sheet loading, Google Form normalisation, date fallback, and calculated load
- `training_app/analytics.py`: volume, estimated 1RM, muscle target sets, and next-session scoring
- `training_app/visualizations.py`: muscle coverage visuals
- `training_app/views.py`: Streamlit screens and tab content

## Future Health Data Direction

Apple Health import is not active in the app right now. iPhone Shortcuts is not rich enough for the detail we want, especially deep sleep and clean activity separation between gym, pickleball, and football.

The better future route is likely an export/import workflow or a dedicated health-data app/export that can preserve workout type, sleep stages, heart-rate series, and activity details.

## Visualization ideas

The current app uses a dependency-free muscle coverage grid because it works well on mobile and is easy to maintain.

More interesting next options:

- Interactive SVG body map using a small JavaScript component
- Front/back body silhouette with colored muscle zones
- Radar chart for push/pull/legs balance
- Calendar heatmap showing training days and muscle focus
- Sankey/network view from exercise to targeted muscles

## How to keep recording

For now, keep using the app form during or after a workout. The minimum useful entry is:

```text
date, exercise, sets, reps, weight
```

If you are in a rush, notes like this are fine:

```text
18 may 26
Bench 3x8 55kg
Lat pulldown 4x10 30kg
Bicep curl 4 sets 15kg, reps unknown
```

Try to record reps whenever possible because volume and estimated strength need reps. If you miss reps, leave them blank and add the original note.

During the workout, record only the lift data:

```text
exercise, sets, reps, weight
```

After the workout, add optional context if you have it:

- duration
- calories
- average heart rate
- max heart rate
- body weight
- whether you took protein
- protein grams
- energy
- motivation
- session quality
- productivity
- sleep
- how you were feeling

## How this becomes both useful and educational

Phase 1: Streamlit + CSV
- Learn basic app structure, forms, CSV persistence, pandas transforms, and charts.
- Practical result: a dashboard you can use immediately.

Phase 2: Phone-friendly gym companion
- Build the `Gym view` around quick decisions: what to train, last set targets, and simple progression nudges.
- Practical result: open it from your phone while the Streamlit server is running on your laptop.

Phase 3: Database and accounts
- Move from CSV to SQLite or Supabase.
- Practical result: more reliable history, easier backups, and a path toward a real hosted app.

Phase 4: Proper mobile web app
- Rebuild the frontend in Next.js or React Native once the data model feels right.
- Practical result: installable phone app experience, faster logging, and better offline support.
