"""
Korsen's training plan, encoded as data.
Edit this file any time your plan changes — the bot always reads live from here.
"""

from datetime import date

START_DATE = date(2026, 9, 14)  # Monday, Week 1, Day 1

MICHIGAN_TRIP = (date(2026, 10, 1), date(2026, 10, 9))  # inclusive

RACE_DATE = date(2026, 11, 7)

# ---------------------------------------------------------------------------
# LIFTING — Planet Fitness, Cane Bay
# ---------------------------------------------------------------------------

LIFT_DAYS = {
    0: {  # Monday
        "name": "Day A — Upper Push",
        "exercises": [
            "Incline DB press — 4x6-10",
            "Machine chest press — 3x8-12",
            "Shoulder press machine — 3x8-12",
            "Seated DB lateral raise — 3x12-20",
            "Overhead rope triceps extension (cable) — 3x10-15",
            "Triceps pushdown (cable) — 2x12-20",
        ],
    },
    2: {  # Wednesday
        "name": "Day B — Lower + Core",
        "exercises": [
            "Smith machine squat — 3x6-10",
            "DB Romanian deadlift — 3x8-12",
            "Leg press — 3x10-15",
            "Leg curl machine — 3x10-15",
            "Calf raise machine — 4x10-15",
            "Cable crunch — 3x12-15",
        ],
    },
    3: {  # Thursday
        "name": "Day C — Upper Pull",
        "exercises": [
            "Lat pulldown, wide grip — 4x8-12",
            "Seated row machine — 3x8-12",
            "Single-arm DB row — 3x10-15",
            "Cable face pull — 3x15-20",
            "Incline DB curl — 3x8-12",
            "Hammer curl — 3x10-15",
        ],
    },
    5: {  # Saturday
        "name": "Day D — Arms, Delts & Core",
        "exercises": [
            "Seated DB lateral raise — 4x12-20",
            "Pec deck fly — 3x10-15",
            "Cable crossover fly or close-grip chest press — 3x8-12",
            "Preacher curl (machine or DB incline) — 3x10-15",
            "Cable overhead triceps extension — 3x10-15",
            "DB spider curl — 2x12-15",
            "Cable crunch — 3x12-15",
            "Reverse crunch — 3x10-15",
        ],
    },
}

# Anytime Fitness swaps used automatically during the Michigan trip
MICHIGAN_SWAPS = {
    "Machine chest press": "Flat or incline DB press",
    "Shoulder press machine": "Seated DB shoulder press",
    "Leg press": "Bulgarian split squat or Smith machine squat",
    "Cable crossover fly or close-grip chest press": "DB fly (bench)",
    "Overhead rope triceps extension (cable)": "DB overhead triceps extension",
    "Triceps pushdown (cable)": "DB overhead triceps extension (2nd set)",
    "Cable face pull": "Band or DB rear delt fly",
    "Preacher curl (machine or DB incline)": "Incline DB curl or concentration curl",
    "Pec deck fly": "Flat DB fly",
    "Seated row machine": "Single-arm DB row",
    "Cable overhead triceps extension": "DB overhead triceps extension",
    "Cable crunch": "Weighted decline sit-up or long-lever plank",
}

# ---------------------------------------------------------------------------
# ALO WELLNESS CLUB
# ---------------------------------------------------------------------------

ALO_DAYS = {
    1: "Alo: Vinyasa flow / mobility (30-45 min). Weeks 1-2: Wellness 101 series.",
    3: "Alo: Pilates or core sculpt (20-30 min). Weeks 1-2: Wellness 101 series.",
    4: "Alo: Yin / deep stretch (30-45 min) — your highest-value flexibility session.",
}

# ---------------------------------------------------------------------------
# RUNNING — 8-week half marathon build, Tue/Fri/Sun distances
# Mon/Wed/Thu/Sat are always the 1-mile streak-keeper minimum.
# ---------------------------------------------------------------------------

RUN_WEEKS = {
    1: {"tue": "3 mi easy (Z2 — slow!)", "fri": "4 mi easy (Z2)", "sun": "6 mi long, Z2"},
    2: {"tue": "4 mi easy (Z2)", "fri": "4 mi easy (Z2)", "sun": "7 mi long, Z2"},
    3: {"tue": "4 mi easy (Z2)", "fri": "5 mi easy (Z2)", "sun": "8 mi long, Z2"},
    4: {"tue": "4 mi easy + 6x20s strides", "fri": "5 mi easy (Z2)", "sun": "9 mi long, Z2"},
    5: {"tue": "4 mi easy + strides", "fri": "5 mi: 1mi warmup, 2-3mi tempo (Z4), 1mi cooldown", "sun": "10 mi long, Z2, last 2mi at goal pace"},
    6: {"tue": "5 mi easy (Z2)", "fri": "6 mi: warmup, 3mi tempo, cooldown", "sun": "11 mi long, Z2, last 2mi at goal pace"},
    7: {"tue": "4 mi easy (Z2)", "fri": "5 mi easy (Z2)", "sun": "8 mi cutback long, Z2"},
    8: {"tue": "3 mi easy + strides", "fri": "2 mi easy, shakeout", "sun": "RACE DAY — 13.1 mi. Go out 9:45-9:50, settle to 9:30 through mi 9, empty the tank from mi 10."},
}

RACE_PACE_TARGETS = "Conservative 2:10 (9:55/mi) · Realistic 2:05 (9:32/mi) · Stretch sub-2:00 (9:09/mi)"

# ---------------------------------------------------------------------------
# DAILY SCHEDULE & NUTRITION TARGETS
# ---------------------------------------------------------------------------

WAKE_TIME = "6:30 AM"
BEDTIME = "11:00 PM"
DEFAULT_RUN_WINDOW = "morning, right after waking"
DEFAULT_LIFT_WINDOW = "around lunch (~12:30 PM)"
WEIGH_IN_WEEKDAY = 0  # Monday

DEFAULT_BODYWEIGHT_LBS = 164.6  # updated automatically once Monday weigh-ins start logging


def water_goal_ml(bodyweight_lbs: float) -> int:
    """
    Standard hydration heuristic: half your bodyweight (lbs) in ounces of water/day.
    At 164.6 lbs that's ~82 oz (~2,425 mL). (Korsen's original spec -- water in mL equal
    to the bodyweight number -- would be ~165 mL/day, far too low to be real; using the
    standard formula instead. Change this function if a different target is wanted.)
    """
    ounces = bodyweight_lbs / 2
    return round(ounces * 29.5735)


def protein_goal_g(bodyweight_lbs: float) -> int:
    return round(bodyweight_lbs)  # ~1g/lb


def get_week_number(today: date) -> int:
    delta_days = (today - START_DATE).days
    week = (delta_days // 7) + 1
    return max(1, min(8, week))


def in_michigan(today: date) -> bool:
    return MICHIGAN_TRIP[0] <= today <= MICHIGAN_TRIP[1]


def get_daily_plan(today: date) -> dict:
    """Returns everything scheduled for a given date."""
    weekday = today.weekday()  # 0=Mon ... 6=Sun
    week_num = get_week_number(today)
    michigan = in_michigan(today)

    plan = {
        "date": today.isoformat(),
        "week_number": week_num,
        "weekday": weekday,
        "in_michigan": michigan,
        "days_to_race": (RACE_DATE - today).days,
        "lift": None,
        "run": None,
        "alo": None,
        "notes": [],
    }

    # Lift
    if weekday in LIFT_DAYS:
        lift = dict(LIFT_DAYS[weekday])
        if michigan:
            lift["exercises"] = [MICHIGAN_SWAPS.get(ex.split(" — ")[0], ex) if ex.split(" — ")[0] in MICHIGAN_SWAPS else ex for ex in lift["exercises"]]
            plan["notes"].append("You're in Michigan — using Anytime Fitness swaps for anything Planet Fitness-specific.")
        plan["lift"] = lift

    # Alo
    if weekday in ALO_DAYS:
        plan["alo"] = ALO_DAYS[weekday]

    # Run
    week_data = RUN_WEEKS.get(week_num, RUN_WEEKS[8])
    if weekday == 1:  # Tuesday
        plan["run"] = week_data["tue"]
    elif weekday == 4:  # Friday
        plan["run"] = week_data["fri"]
    elif weekday == 6:  # Sunday
        plan["run"] = week_data["sun"]
        if today == RACE_DATE:
            plan["notes"].append(f"RACE DAY. Targets: {RACE_PACE_TARGETS}")
    else:
        plan["run"] = "1 mi easy — streak keeper, non-negotiable"

    if michigan and not plan["notes"]:
        plan["notes"].append("You're in Michigan on the Anytime Fitness membership this week.")

    return plan
