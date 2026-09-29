import html
import os
import sqlite3
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
DB_PATH = ROOT / "fitbuddy.db"

app = FastAPI(title="FitBuddy AI Fitness Plan Generator")


def init_db():
    with sqlite3.connect(DB_PATH) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT UNIQUE NOT NULL,
                username TEXT NOT NULL,
                age INTEGER NOT NULL,
                weight REAL NOT NULL,
                goal TEXT NOT NULL,
                intensity TEXT NOT NULL,
                plan TEXT NOT NULL,
                feedback TEXT DEFAULT '',
                created_at TEXT NOT NULL
            )
        """)


def safe(value):
    return html.escape(str(value))


def make_plan(name, age, goal, intensity):
    key = os.getenv("GOOGLE_API_KEY", "").strip()
    if key:
        try:
            from google import genai
            client = genai.Client(api_key=key)
            response = client.models.generate_content(
                model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
                contents=(
                    f"Create a balanced, safe beginner-friendly 7-day fitness plan for {name}, "
                    f"age {age}, goal {goal}, preferred intensity {intensity}. Include warm-ups, "
                    "gentle activities, and recovery. Avoid extreme diets and medical claims."
                ),
            )
            if response.text:
                return response.text
        except Exception:
            pass

    return f"""7-DAY ACTIVITY PLAN
Goal: {goal} | Preferred intensity: {intensity}

Day 1 — Full-body basics
Warm up with 5 minutes of easy walking. Try comfortable chair squats, wall push-ups, glute bridges, and gentle marching. Finish with relaxed stretching.

Day 2 — Easy cardio
Take a comfortable walk, cycle, or choose another enjoyable movement for 15–25 minutes. Keep a pace where you can still talk.

Day 3 — Strength and balance
After warming up, try supported lunges, backpack rows, calf raises, and bird-dogs at a comfortable level. Rest between sets.

Day 4 — Recovery
Rest or take a gentle walk. Recovery is an important part of a fitness routine.

Day 5 — Full-body movement
Repeat a few comfortable movements from earlier in the week. Focus on control rather than speed.

Day 6 — Enjoyable activity
Choose dancing, walking, cycling, a sport, or another activity you enjoy.

Day 7 — Rest and reflect
Take a rest day and consider which activities felt comfortable.

Safety: Begin gently, adjust to your ability, and stop if you feel pain, dizziness, or unusual discomfort. This general plan is not medical advice."""


def page(title, body):
    return HTMLResponse(f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{safe(title)}</title>
<style>
:root{{font-family:Arial,sans-serif;color:#193629;background:#f2f7f3}}
*{{box-sizing:border-box}}body{{margin:0;background:linear-gradient(135deg,#e4f7eb,#f7faf8);min-height:100vh}}
main{{max-width:850px;margin:0 auto;padding:38px 18px}}header{{text-align:center;padding:18px 0 25px}}
h1{{font-size:clamp(2.3rem,7vw,4rem);margin:5px;color:#17643c}}h1 span{{color:#39a66b}}
header p{{color:#5d7365}}.card{{background:white;border:1px solid #e1ebe4;border-radius:18px;padding:26px;margin:16px 0;box-shadow:0 10px 30px #173c2410}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}label{{display:block;font-weight:600;font-size:14px;margin-bottom:15px}}
input,select,textarea{{display:block;width:100%;padding:12px;margin-top:7px;border:1px solid #ccdacf;border-radius:9px;font:inherit}}
button,.btn{{background:#21864f;color:white;border:0;border-radius:10px;padding:13px 18px;font-weight:bold;cursor:pointer;text-decoration:none;display:inline-block}}
.full{{width:100%;grid-column:1/-1}}.plan{{white-space:pre-wrap;line-height:1.7;font-size:15px;color:#344c3d}}
a{{color:#21864f}}footer{{text-align:center;color:#75867b;padding:20px}}.error{{background:#fff0ef;color:#a22;padding:12px;border-radius:9px}}
@media(max-width:600px){{.grid{{grid-template-columns:1fr}}.full{{grid-column:auto}}}}
</style></head><body><main><header><p>YOUR PERSONAL FITNESS COMPANION</p><h1>FitBuddy <span>AI</span></h1><p>Build a balanced activity routine around your goals.</p></header>{body}<footer>Move at a comfortable pace. Rest is part of progress.</footer></main></body></html>""")


@app.on_event("startup")
def startup():
    init_db()


@app.get("/", response_class=HTMLResponse)
def home():
    body = """
<section class="card"><h2>Create your 7-day plan</h2>
<form action="/generate" method="post">
<div class="grid">
<label>Name<input name="username" maxlength="100" required></label>
<label>Unique user ID<input name="user_id" maxlength="80" required></label>
<label>Age<input type="number" name="age" min="1" max="120" required></label>
<label>Weight (kg)<input type="number" name="weight" min="1" step="0.1" required></label>
<label>Goal<select name="goal"><option>General wellness</option><option>Build strength</option><option>Improve fitness</option><option>Flexibility</option></select></label>
<label>Intensity<select name="intensity"><option>Beginner</option><option>Gentle</option><option>Moderate</option></select></label>
<button class="full" type="submit">Generate my plan</button>
</div></form></section><p style="text-align:center"><a href="/admin">View saved users</a></p>"""
    return page("FitBuddy AI", body)


@app.post("/generate", response_class=HTMLResponse)
async def generate(request: Request):
    form = await request.form()
    username = str(form.get("username", "")).strip()
    user_id = str(form.get("user_id", "")).strip()
    goal = str(form.get("goal", "General wellness"))
    intensity = str(form.get("intensity", "Beginner"))
    try:
        age = int(str(form.get("age", "")))
        weight = float(str(form.get("weight", "")))
        if not username or not user_id or not 1 <= age <= 120 or weight <= 0:
            raise ValueError()
    except ValueError:
        return page("Check your details", '<section class="card"><p class="error">Please enter valid details.</p><a href="/">Go back</a></section>')

    plan = make_plan(username, age, goal, intensity)
    with sqlite3.connect(DB_PATH) as con:
        con.execute("""INSERT INTO users(user_id,username,age,weight,goal,intensity,plan,created_at)
        VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET username=excluded.username,
        age=excluded.age,weight=excluded.weight,goal=excluded.goal,intensity=excluded.intensity,
        plan=excluded.plan,feedback=''""",
        (user_id, username, age, weight, goal, intensity, plan, datetime.now().isoformat(timespec="seconds")))
    body = f"""<section class="card"><h2>Your 7-day plan</h2><p>Plan for {safe(username)} · ID: {safe(user_id)}</p><div class="plan">{safe(plan)}</div></section>
<section class="card"><h2>Nutrition and recovery</h2><p>Choose regular, balanced meals with a variety of foods, drink water throughout the day, and allow time for rest. Avoid extreme restrictions.</p>
<h3>Request an adjustment</h3><form action="/feedback" method="post"><input type="hidden" name="user_id" value="{safe(user_id)}"><label>What would you like to change?<textarea name="feedback" rows="3" required></textarea></label><button>Update plan</button></form></section><p><a href="/">Create another plan</a> · <a href="/admin">Saved users</a></p>"""
    return page("Your FitBuddy Plan", body)


@app.post("/feedback", response_class=HTMLResponse)
async def feedback(request: Request):
    form = await request.form()
    user_id = str(form.get("user_id", "")).strip()
    note = str(form.get("feedback", "")).strip()
    with sqlite3.connect(DB_PATH) as con:
        row = con.execute("SELECT username,age,goal,intensity,plan FROM users WHERE user_id=?", (user_id,)).fetchone()
        if not row:
            return page("User not found", '<section class="card"><p>User not found. Please generate a plan first.</p><a href="/">Home</a></section>')
        username, age, goal, intensity, old_plan = row
        updated = old_plan + "\\n\\nYour requested adjustment: " + note + "\\nPlease make changes gradually and keep recovery days."
        con.execute("UPDATE users SET plan=?,feedback=? WHERE user_id=?", (updated, note, user_id))
    body = f'<section class="card"><h2>Updated plan</h2><p>Plan for {safe(username)}</p><div class="plan">{safe(updated)}</div></section><p><a href="/">Home</a> · <a href="/admin">Saved users</a></p>'
    return page("Updated FitBuddy Plan", body)


@app.get("/admin", response_class=HTMLResponse)
def admin():
    with sqlite3.connect(DB_PATH) as con:
        rows = con.execute("SELECT user_id,username,goal,intensity,created_at FROM users ORDER BY id DESC").fetchall()
    if not rows:
        table = "<p>No saved users yet.</p>"
    else:
        trs = "".join(f"<tr><td>{safe(r[0])}</td><td>{safe(r[1])}</td><td>{safe(r[2])}</td><td>{safe(r[3])}</td><td>{safe(r[4])}</td></tr>" for r in rows)
        table = f"<div style='overflow:auto'><table border='1' cellpadding='10' style='border-collapse:collapse;width:100%'><tr><th>User ID</th><th>Name</th><th>Goal</th><th>Intensity</th><th>Created</th></tr>{trs}</table></div>"
    return page("FitBuddy Admin", f'<section class="card"><h2>Saved users</h2>{table}<p><a href="/">Back to home</a></p></section>')
