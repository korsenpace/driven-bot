import os
import re
import json
from datetime import date

import requests
from flask import Flask, request, Response
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
import anthropic

from plan_data import (
    get_daily_plan,
    WAKE_TIME,
    BEDTIME,
    DEFAULT_RUN_WINDOW,
    DEFAULT_LIFT_WINDOW,
    WEIGH_IN_WEEKDAY,
    DEFAULT_BODYWEIGHT_LBS,
    water_goal_ml,
    protein_goal_g,
)

app = Flask(__name__)

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
TWILIO_ACCOUNT_SID = os.environ["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN = os.environ["TWILIO_AUTH_TOKEN"]
TWILIO_FROM_NUMBER = os.environ["TWILIO_FROM_NUMBER"]
MY_PHONE_NUMBER = os.environ["MY_PHONE_NUMBER"]
CRON_SECRET = os.environ["CRON_SECRET"]
UPSTASH_URL = os.environ["UPSTASH_REDIS_REST_URL"]
UPSTASH_TOKEN = os.environ["UPSTASH_REDIS_REST_TOKEN"]

claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# ---------------------------------------------------------------------------
# Tiny persistence layer (Upstash Redis REST API — free tier, no server needed)
# ---------------------------------------------------------------------------

def _redis_headers():
    return {"Authorization": f"Bearer {UPSTASH_TOKEN}"}


def redis_get(key):
    r = requests.get(f"{UPSTASH_URL}/get/{key}", headers=_redis_headers())
    result = r.json().get("result")
    return json.loads(result) if result else None


def redis_set(key, value, ex_seconds=None):
    url = f"{UPSTASH_URL}/set/{key}"
    if ex_seconds:
        url += f"?EX={ex_seconds}"
    requests.post(url, headers=_redis_headers(), data=json.dumps(value))


def today_state_key(d: date) -> str:
    return f"state:{d.isoformat()}"


def get_today_state(d: date) -> dict:
    return redis_get(today_state_key(d)) or {"awaiting": None}


def set_today_state(d: date, state: dict):
    redis_set(today_state_key(d), state, ex_seconds=60 * 60 * 30)  # expires after 30h, harmless


def get_bodyweight() -> float:
    val = redis_get("bodyweight:latest")
    return float(val) if val else DEFAULT_BODYWEIGHT_LBS


def set_bodyweight(lbs: float):
    redis_set("bodyweight:latest", lbs)


# ---------------------------------------------------------------------------
# Claude persona
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are Drivent — Korsen's training mentor, texting him over SMS. You are scientifically \
sharp: you know exercise physiology, hypertrophy, endurance training, and sports nutrition well, and when he \
asks you something you teach him the real mechanism, not a dumbed-down answer. But every message you send is \
still a text message, not an essay — short paragraphs, no walls of text, get to the point fast.

Context you always know:
- Half marathon Nov 7, 2026. Lifting at Planet Fitness Cane Bay (or Anytime Fitness during Michigan trips). \
Alo Wellness Club for flexibility. Daily 1-mile running minimum. Building toward 185 lbs.
- He wakes at {wake}, goes to bed at {bed}. Runs happen in the morning right after waking. Lifting happens \
around lunch. These are defaults — if he tells you a different time applies today, use that instead, just \
for today, unless he says to change the standing schedule.
- Weigh-ins happen Monday mornings.
- Daily targets: ~{water} mL water, ~{protein}g protein, 3 meals.

Style rules:
- No fluff, no forced enthusiasm, no "let's crush it" energy. Talk like a smart, direct coach who respects \
his time.
- Never invent information you don't have — if you don't know something about his day (weather, a personal \
appointment, etc.), don't guess at it.
- When he asks a real question or wants to learn something, actually teach it — mechanisms, not just \
conclusions. This is where you can go longer if the topic needs it.
"""


def system_prompt() -> str:
    bw = get_bodyweight()
    return SYSTEM_PROMPT.format(
        wake=WAKE_TIME, bed=BEDTIME, water=water_goal_ml(bw), protein=protein_goal_g(bw)
    )


def build_plan_context(plan: dict) -> str:
    lines = [f"Today is {plan['date']}, week {plan['week_number']} of 8, {plan['days_to_race']} days to race."]
    if plan["lift"]:
        lines.append(f"LIFT ({DEFAULT_LIFT_WINDOW}) — {plan['lift']['name']}:")
        lines.extend(f"  {ex}" for ex in plan["lift"]["exercises"])
    else:
        lines.append("No lift scheduled today.")
    lines.append(f"RUN ({DEFAULT_RUN_WINDOW}) — {plan['run']}")
    if plan["alo"]:
        lines.append(f"ALO — {plan['alo']}")
    for n in plan["notes"]:
        lines.append(f"NOTE — {n}")
    return "\n".join(lines)


def ask_claude(user_content: str, max_tokens: int = 350) -> str:
    msg = claude.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=max_tokens,
        system=system_prompt(),
        messages=[{"role": "user", "content": user_content}],
    )
    return msg.content[0].text


def send_sms(body: str):
    twilio_client.messages.create(body=body, from_=TWILIO_FROM_NUMBER, to=MY_PHONE_NUMBER)


# ---------------------------------------------------------------------------
# Cron-triggered proactive messages
# ---------------------------------------------------------------------------

@app.route("/morning-checkin", methods=["GET", "POST"])
def morning_checkin():
    """Fire around 6:30 AM."""
    if request.args.get("key") != CRON_SECRET:
        return Response("forbidden", status=403)

    today = date.today()
    state = {"awaiting": "obstacle"}
    set_today_state(today, state)

    send_sms("Morning. Anything getting in the way of today's training?")
    return {"sent": "morning_checkin"}


@app.route("/evening-checkin", methods=["GET", "POST"])
def evening_checkin():
    """Fire around 10:00 PM (1hr before bed)."""
    if request.args.get("key") != CRON_SECRET:
        return Response("forbidden", status=403)

    today = date.today()
    state = get_today_state(today)
    state["awaiting"] = "evening"
    set_today_state(today, state)

    send_sms(
        "Winding down time. How are you feeling, did you eat enough today (water/protein/3 meals), "
        "and how do the muscles you trained feel?"
    )
    return {"sent": "evening_checkin"}


# ---------------------------------------------------------------------------
# Incoming texts
# ---------------------------------------------------------------------------

@app.route("/sms", methods=["POST"])
def incoming_sms():
    incoming_msg = request.form.get("Body", "").strip()
    today = date.today()
    plan = get_daily_plan(today)
    plan_context = build_plan_context(plan)
    state = get_today_state(today)
    awaiting = state.get("awaiting")

    if awaiting == "obstacle":
        state["obstacle"] = incoming_msg
        is_weighin_day = today.weekday() == WEIGH_IN_WEEKDAY
        prompt = (
            f"Today's plan:\n{plan_context}\n\n"
            f"Korsen just told you what might get in the way today: \"{incoming_msg}\"\n\n"
            f"Reply with today's overview: acknowledge the obstacle in one short line only if it actually "
            f"affects training (otherwise skip straight past it), then give the exact lift plan with "
            f"sets/reps and its time window, the run and its time window, and the Alo class if any. "
            + ("End by asking for his weigh-in number since it's Monday." if is_weighin_day else "")
        )
        reply_text = ask_claude(prompt)
        state["awaiting"] = "weighin" if is_weighin_day else None
        set_today_state(today, state)

    elif awaiting == "weighin":
        match = re.search(r"(\d+(\.\d+)?)", incoming_msg)
        if match:
            weight = float(match.group(1))
            set_bodyweight(weight)
            new_water = water_goal_ml(weight)
            new_protein = protein_goal_g(weight)
            reply_text = f"Logged — {weight} lbs. Today's targets: ~{new_water} mL water, ~{new_protein}g protein."
            state["awaiting"] = None
            set_today_state(today, state)
        else:
            reply_text = "Didn't catch a number in that — what'd the scale say this morning?"

    elif awaiting == "evening":
        state["awaiting"] = None
        set_today_state(today, state)
        prompt = (
            f"Today's plan was:\n{plan_context}\n\n"
            f"Korsen's evening check-in response: \"{incoming_msg}\"\n\n"
            f"Respond briefly — react to what he said (feeling, food, soreness), note anything worth "
            f"flagging for tomorrow (e.g. if a muscle group needs more recovery, if he under-ate), and "
            f"keep it to 2-4 sentences. No lecture."
        )
        reply_text = ask_claude(prompt)

    else:
        # General mentor mode — questions, logging, teaching, anything
        prompt = f"Today's plan for context:\n{plan_context}\n\nKorsen just texted: \"{incoming_msg}\"\n\nReply as Drivent."
        reply_text = ask_claude(prompt, max_tokens=500)

    twiml = MessagingResponse()
    twiml.message(reply_text)
    return Response(str(twiml), mimetype="application/xml")


@app.route("/", methods=["GET"])
def health():
    return {"status": "Drivent is running"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
