from __future__ import annotations

import os
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = APP_DIR / "data"
WORKOUTS_PATH = DATA_DIR / "workouts.csv"
LEGACY_FORM_PATH = DATA_DIR / "legacy_google_form.csv"
FORM_SCRIPT_PATH = APP_DIR / "google_form_creator.gs"
DEFAULT_GOOGLE_SHEET_URL = os.environ.get("TRAINING_LAB_GOOGLE_SHEET_URL", "")

# Extra base load added when a machine/barbell lift is logged as "per side".
# Edit this one mapping when a machine's starting sled/bar weight is different.
PER_SIDE_BASE_LOAD_KG = {
    "Bench press": 20.0,
    "Incline bench press": 20.0,
    "Leg press": 47.0,
    "Leg press calf raise": 47.0,
}

EXERCISES = {
    "Bench press": "Chest",
    "Seated lateral raise machine": "Shoulders",
    "Barbell bicep curl": "Biceps",
    "Dumbbell bicep curl": "Biceps",
    "Hammer curl": "Biceps",
    "Single-arm shoulder raise": "Shoulders",
    "Seated shoulder press": "Shoulders",
    "Lat pulldown": "Back",
    "Seated row": "Back",
    "Tricep pulldown": "Triceps",
    "Overhead dumbbell tricep extension": "Triceps",
    "Pull-up": "Back",
    "Rear delt machine": "Shoulders",
    "Leg extension": "Legs",
    "Incline bench press": "Chest",
    "Incline dumbbell press": "Chest",
    "Flat dumbbell press": "Chest",
    "Pectoral fly": "Chest",
    "Reverse pec deck": "Shoulders",
    "Incline T-bar row": "Back",
    "Leg press": "Legs",
    "Leg press calf raise": "Legs",
    "Cycling": "Cardio",
    "Stationary bike": "Cardio",
}

EXERCISE_CATEGORIES = {
    "Push": [
        "Bench press",
        "Incline bench press",
        "Incline dumbbell press",
        "Flat dumbbell press",
        "Pectoral fly",
        "Seated shoulder press",
        "Seated lateral raise machine",
        "Single-arm shoulder raise",
        "Tricep pulldown",
        "Overhead dumbbell tricep extension",
    ],
    "Pull": [
        "Lat pulldown",
        "Seated row",
        "Incline T-bar row",
        "Pull-up",
        "Rear delt machine",
        "Reverse pec deck",
        "Barbell bicep curl",
        "Dumbbell bicep curl",
        "Hammer curl",
    ],
    "Legs": [
        "Leg extension",
        "Leg press",
        "Leg press calf raise",
    ],
    "Cardio": [
        "Cycling",
        "Stationary bike",
    ],
}

MUSCLE_GROUPS = [
    "Chest",
    "Back",
    "Shoulders",
    "Biceps",
    "Triceps",
    "Legs",
    "Core",
    "Cardio",
    "Full body",
]

MUSCLE_TARGETS = {
    "bench press": {
        "Chest": 1.0,
        "Front delts": 0.45,
        "Triceps": 0.45,
    },
    "incline bench press": {
        "Upper chest": 1.0,
        "Chest": 0.65,
        "Front delts": 0.55,
        "Triceps": 0.4,
    },
    "incline dumbbell press": {
        "Upper chest": 1.0,
        "Chest": 0.7,
        "Front delts": 0.45,
        "Triceps": 0.35,
    },
    "flat dumbbell press": {
        "Chest": 1.0,
        "Front delts": 0.35,
        "Triceps": 0.35,
    },
    "pectoral fly": {
        "Chest": 1.0,
        "Upper chest": 0.25,
        "Front delts": 0.15,
    },
    "seated lateral raise machine": {
        "Side delts": 1.0,
        "Traps": 0.2,
    },
    "single-arm shoulder raise": {
        "Side delts": 1.0,
        "Front delts": 0.25,
        "Traps": 0.15,
    },
    "seated shoulder press": {
        "Front delts": 1.0,
        "Side delts": 0.55,
        "Triceps": 0.55,
        "Upper chest": 0.2,
    },
    "barbell bicep curl": {
        "Biceps": 1.0,
        "Forearms": 0.35,
    },
    "dumbbell bicep curl": {
        "Biceps": 1.0,
        "Forearms": 0.35,
    },
    "hammer curl": {
        "Brachialis": 1.0,
        "Biceps": 0.65,
        "Forearms": 0.55,
    },
    "lat pulldown": {
        "Lats": 1.0,
        "Upper back": 0.45,
        "Biceps": 0.45,
        "Rear delts": 0.2,
    },
    "seated row": {
        "Upper back": 1.0,
        "Lats": 0.7,
        "Rear delts": 0.45,
        "Biceps": 0.4,
    },
    "pull-up": {
        "Lats": 1.0,
        "Upper back": 0.45,
        "Biceps": 0.45,
        "Core": 0.2,
    },
    "tricep pulldown": {
        "Triceps": 1.0,
    },
    "overhead dumbbell tricep extension": {
        "Triceps": 1.0,
    },
    "rear delt machine": {
        "Rear delts": 1.0,
        "Upper back": 0.35,
        "Traps": 0.25,
    },
    "reverse pec deck": {
        "Rear delts": 1.0,
        "Upper back": 0.35,
        "Traps": 0.2,
    },
    "leg extension": {
        "Quads": 1.0,
    },
    "leg press": {
        "Quads": 1.0,
        "Glutes": 0.65,
        "Hamstrings": 0.35,
        "Calves": 0.15,
    },
    "leg press calf raise": {
        "Calves": 1.0,
    },
    "incline t-bar row": {
        "Upper back": 1.0,
        "Lats": 0.65,
        "Rear delts": 0.5,
        "Biceps": 0.35,
        "Traps": 0.25,
    },
    "cycling": {
        "Cardio": 1.0,
        "Quads": 0.45,
        "Glutes": 0.25,
        "Calves": 0.25,
        "Hamstrings": 0.15,
    },
    "stationary bike": {
        "Cardio": 1.0,
        "Quads": 0.45,
        "Glutes": 0.25,
        "Calves": 0.25,
        "Hamstrings": 0.15,
    },
}

MUSCLE_SECTIONS = {
    "Push": ["Chest", "Upper chest", "Front delts", "Side delts", "Triceps"],
    "Pull": ["Lats", "Upper back", "Rear delts", "Traps", "Biceps", "Brachialis", "Forearms"],
    "Legs / Core": ["Quads", "Hamstrings", "Glutes", "Calves", "Core"],
    "Conditioning": ["Cardio"],
}

ALL_TRACKED_MUSCLES = [muscle for muscles in MUSCLE_SECTIONS.values() for muscle in muscles]

COLUMNS = [
    "date",
    "start_time",
    "session_type",
    "exercise",
    "muscle_group",
    "sets",
    "reps",
    "weight_kg",
    "weight_basis",
    "rpe",
    "duration_min",
    "calories",
    "avg_heart_rate",
    "max_heart_rate",
    "body_weight_kg",
    "protein_taken",
    "protein_grams",
    "energy",
    "motivation",
    "session_quality",
    "productivity",
    "sleep_hours",
    "feeling",
    "notes",
]

COLUMN_ALIASES = {
    "date": "date",
    "workout date": "date",
    "start time": "start_time",
    "session": "session_type",
    "session type": "session_type",
    "exercise": "exercise",
    "exercise name": "exercise",
    "other exercise": "other_exercise",
    "muscle group": "muscle_group",
    "sets": "sets",
    "reps": "reps",
    "weight kg": "weight_kg",
    "weight (kg)": "weight_kg",
    "weight_kg": "weight_kg",
    "weight basis": "weight_basis",
    "rpe": "rpe",
    "duration min": "duration_min",
    "duration (min)": "duration_min",
    "calories": "calories",
    "avg heart rate": "avg_heart_rate",
    "average heart rate": "avg_heart_rate",
    "max heart rate": "max_heart_rate",
    "body weight kg": "body_weight_kg",
    "body weight (kg)": "body_weight_kg",
    "protein taken": "protein_taken",
    "took protein": "protein_taken",
    "protein grams": "protein_grams",
    "energy": "energy",
    "motivation": "motivation",
    "session quality": "session_quality",
    "gym session quality": "session_quality",
    "productivity": "productivity",
    "felt productive": "productivity",
    "sleep hours": "sleep_hours",
    "sleep (hours)": "sleep_hours",
    "feeling": "feeling",
    "how i am feeling": "feeling",
    "how im feeling": "feeling",
    "notes": "notes",
}
