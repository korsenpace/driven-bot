# Drivent — Your Training Mentor Bot

A real phone number that runs your whole day: asks what might get in the way each
morning, tells you the exact plan once you answer, handles Monday weigh-ins,
checks in on you an hour before bed, and answers anything you ask it like a
sharp, no-fluff coach.

## How the day flows

1. **6:30 AM** — Drivent texts: "Anything getting in the way of today's training?"
2. **You reply** — even just "no" — and it sends back the exact plan: lift
   (with sets/reps) around lunch, run in the morning, Alo class if scheduled,
   and a note if something unusual is happening (Michigan week, race day, etc.)
3. **Mondays only** — after the plan, it asks for your weigh-in number. Reply
   with the number and it logs it and updates your water/protein targets.
4. **10:00 PM** — it checks in: how you're feeling, did you eat enough
   (water/protein/3 meals), how the muscles you trained feel.
5. **Any other time** — text it anything. Questions, "teach me about X,"
   logging a note, whatever. It answers as a knowledgeable mentor, not a
   scripted bot.

## What you're building

- **`plan_data.py`** — your training plan, schedule defaults, and nutrition
  targets as data. Edit any time things change.
- **`app.py`** — the bot. Handles the morning/evening cron triggers and all
  incoming texts, and remembers what stage of the day you're in using a small
  free hosted database (Upstash Redis).
- **`requirements.txt`** — Python dependencies.

## Setup (about 30-40 minutes)

### 1. Anthropic API key
console.anthropic.com → API Keys → Create Key (no expiration). Save as
`ANTHROPIC_API_KEY`.

### 2. Twilio number
twilio.com → buy an SMS-capable number (~$1.15/mo). From the console, grab
your **Account SID** and **Auth Token**.

### 3. Upstash Redis (free) — this is what gives Drivent memory
1. Go to upstash.com, sign up free
2. Create a new Redis database (any region close to you, e.g. US-East)
3. On the database's detail page, find the **REST API** section
4. Copy the **UPSTASH_REDIS_REST_URL** and **UPSTASH_REDIS_REST_TOKEN** values
   shown there — these go straight into your env vars below

### 4. Deploy on Render.com (free tier)
1. Push this folder to a GitHub repo (private is fine)
2. Render.com → New → Web Service → connect the repo
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app`
5. Environment variables:
   - `ANTHROPIC_API_KEY`
   - `TWILIO_ACCOUNT_SID`
   - `TWILIO_AUTH_TOKEN`
   - `TWILIO_FROM_NUMBER` — e.g. `+18433766977`
   - `MY_PHONE_NUMBER` — your cell, e.g. `+18435559876`
   - `CRON_SECRET` — any password you make up
   - `UPSTASH_REDIS_REST_URL`
   - `UPSTASH_REDIS_REST_TOKEN`
6. Deploy — you'll get a URL like `https://drivent-xyz.onrender.com`

### 5. Connect Twilio's webhook
Twilio Console → Phone Numbers → your number → Messaging config → "A message
comes in" → `https://drivent-xyz.onrender.com/sms` (method POST) → Save.

Text the number "hey" to confirm it replies.

### 6. Set up the two daily cron triggers
Use cron-job.org (free):

**Morning check-in** — new cron job:
- URL: `https://drivent-xyz.onrender.com/morning-checkin?key=YOUR_CRON_SECRET`
- Schedule: daily, 6:30 AM, your timezone (America/New_York)

**Evening check-in** — new cron job:
- URL: `https://drivent-xyz.onrender.com/evening-checkin?key=YOUR_CRON_SECRET`
- Schedule: daily, 10:00 PM, your timezone

That's the whole thing. Every morning it asks what's in your way, gives you
the plan once you answer, and every night it checks in before bed.

## Notes

- **Render free tier sleeps when idle** — cron hits wake it up, but the very
  first reply after a quiet stretch might take 10-20 seconds.
- **If you don't reply to the morning question**, the plan just doesn't send
  automatically — it's waiting on your answer. If that's annoying, text it
  anything ("no") whenever you get to it and it'll catch up.
- **Water goal** currently uses the standard "half your bodyweight in ounces"
  formula, not a literal bodyweight-in-mL number — see the comment in
  `plan_data.py` if you want it changed.
- **Updating the plan after Nov 7**: edit `plan_data.py`, push to GitHub,
  Render auto-redeploys.
