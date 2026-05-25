# Training Lab

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
- Single-arm shoulder raise
- Seated shoulder press
- Lat pulldown
- Seated row
- Tricep pulldown
- Overhead dumbbell tricep extension
- Pull-up
- Rear delt machine
- Leg extension

Workout data is stored in `data/workouts.csv`.

## Google Form logging

The gym-friendly workflow is:

1. Submit one Google Form response per gym session.
2. Fill up to 6 exercise blocks as you finish each exercise.
2. The form writes to a linked Google Sheet.
3. Paste the sheet CSV export URL into the dashboard sidebar.
4. The dashboard uses that sheet instead of the local CSV.

To create the form, use `google_form_creator.gs` in Google Apps Script. Detailed steps are in `docs/google_form_setup.md`.

The Google Sheet stores each session as one wide row, with columns like `Exercise 1`, `Sets 1`, `Exercise 2`, `Sets 2`, and so on. The dashboard converts those exercise blocks into one long-format analysis row per exercise.

You can also submit a later update with no exercises, for example body weight or protein later in the day. The dashboard stores that as a zero-set `Session update` row so recovery data is kept without changing muscle-volume charts.

For Streamlit to read the sheet, share it as `Anyone with the link can view` or publish it to the web.

## Muscle target logic

The app maps each exercise to weighted target muscles. For example:

- Bench press: chest, front delts, triceps
- Incline bench press: upper chest, chest, front delts, triceps
- Lat pulldown and pull-up: lats, upper back, biceps
- Seated row: upper back, lats, rear delts, biceps
- Lateral raises: side delts
- Shoulder press: front delts, side delts, triceps
- Bicep curls: biceps and forearms
- Tricep pulldown and overhead tricep extension: triceps
- Rear delt machine: rear delts, upper back, traps
- Leg extension: quads
- Leg press: quads, glutes, hamstrings, calves
- Leg press calf raise: calves
- Incline T-bar row: upper back, lats, rear delts, biceps, traps
- Cycling: cardio, quads, glutes, calves, hamstrings

The dashboard uses this to estimate target sets per muscle over the last 14 days and suggest what looks most due.

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
