"""
DinkLab — Flask backend
A personal pickleball portfolio + film room + content planner.
All data stored locally as JSON. AI analysis via LM Studio (OpenAI-compatible local API).
"""

import json
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

import requests
from flask import Flask, jsonify, render_template, request, send_from_directory
from werkzeug.utils import secure_filename

# ---------- Config ----------
def resource_path() -> Path:
    """Resolve paths whether running from source or packaged by PyInstaller."""
    if getattr(sys, "frozen", False):
        # Running inside PyInstaller bundle — files are in _MEIPASS
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


def user_data_dir() -> Path:
    """User-writable directory for data + uploads. Persists across app updates."""
    if getattr(sys, "frozen", False):
        # Packaged: store under the user's home so data survives reinstalls
        home = Path.home()
        if sys.platform == "darwin":
            base = home / "Library" / "Application Support" / "DinkLab"
        elif sys.platform == "win32":
            base = Path(os.environ.get("APPDATA", home)) / "DinkLab"
        else:
            base = home / ".dinklab"
        base.mkdir(parents=True, exist_ok=True)
        return base
    return Path(__file__).resolve().parent.parent


BASE_DIR = resource_path()
USER_DIR = user_data_dir()
DATA_DIR = USER_DIR / "data"
UPLOAD_DIR = USER_DIR / "uploads"
TEMPLATE_DIR = BASE_DIR / "frontend" / "templates"
STATIC_DIR = BASE_DIR / "frontend" / "static"

DATA_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_VIDEO_EXT = {"mp4", "mov", "webm", "mkv"}
ALLOWED_IMAGE_EXT = {"jpg", "jpeg", "png", "webp", "gif"}
MAX_UPLOAD_MB = 500

# LM Studio defaults — override via env if needed
LM_STUDIO_URL = os.environ.get("LM_STUDIO_URL", "http://localhost:1234/v1/chat/completions")
LM_STUDIO_MODEL = os.environ.get("LM_STUDIO_MODEL", "local-model")

app = Flask(__name__, template_folder=str(TEMPLATE_DIR), static_folder=str(STATIC_DIR))
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024


# ---------- Storage helpers ----------
def load(name: str, default):
    """Load JSON file from data dir, returning default if missing."""
    path = DATA_DIR / f"{name}.json"
    if not path.exists():
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return default


def save(name: str, data) -> None:
    """Save data to JSON file in data dir."""
    path = DATA_DIR / f"{name}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


def allowed(filename: str, allowed_set: set) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_set


# ---------- Page route ----------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_DIR, filename)


# ---------- GEAR API ----------
@app.route("/api/gear", methods=["GET"])
def get_gear():
    return jsonify(load("gear", []))


@app.route("/api/gear", methods=["POST"])
def add_gear():
    items = load("gear", [])
    payload = request.form.to_dict()

    photo_url = None
    if "photo" in request.files:
        f = request.files["photo"]
        if f and f.filename and allowed(f.filename, ALLOWED_IMAGE_EXT):
            ext = f.filename.rsplit(".", 1)[1].lower()
            fname = f"gear_{uuid.uuid4().hex}.{ext}"
            f.save(UPLOAD_DIR / fname)
            photo_url = f"/uploads/{fname}"

    if not photo_url:
        external_url = payload.get("external_photo_url", "").strip()
        if external_url:
            try:
                import urllib.request as ureq
                ext = external_url.split("?")[0].rsplit(".", 1)[-1].lower()
                if ext not in ALLOWED_IMAGE_EXT:
                    ext = "jpg"
                fname = f"gear_{uuid.uuid4().hex}.{ext}"
                req = ureq.Request(external_url, headers={"User-Agent": "Mozilla/5.0"})
                with ureq.urlopen(req, timeout=10) as resp:
                    (UPLOAD_DIR / fname).write_bytes(resp.read())
                photo_url = f"/uploads/{fname}"
            except Exception:
                pass

    item = {
        "id": uuid.uuid4().hex,
        "category": payload.get("category", "paddle"),
        "name": payload.get("name", "").strip(),
        "brand": payload.get("brand", "").strip(),
        "specs": payload.get("specs", "").strip(),
        "notes": payload.get("notes", "").strip(),
        "started_using": payload.get("started_using", ""),
        "photo_url": photo_url,
        "created_at": datetime.utcnow().isoformat(),
    }
    items.append(item)
    save("gear", items)
    return jsonify(item), 201


@app.route("/api/gear/image-search")
def gear_image_search():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"images": []})
    try:
        from ddgs import DDGS
        results = DDGS().images(q, max_results=5, safesearch="on")
        images = [
            {"url": r["image"], "thumb": r.get("thumbnail") or r["image"]}
            for r in results if r.get("image")
        ]
        return jsonify({"images": images[:4]})
    except Exception as e:
        return jsonify({"images": [], "error": str(e)})


@app.route("/api/gear/<item_id>", methods=["DELETE"])
def delete_gear(item_id):
    items = load("gear", [])
    items = [i for i in items if i["id"] != item_id]
    save("gear", items)
    return jsonify({"ok": True})


# ---------- FILM ROOM API ----------
@app.route("/api/films", methods=["GET"])
def get_films():
    return jsonify(load("films", []))


@app.route("/api/films", methods=["POST"])
def add_film():
    films = load("films", [])
    title = request.form.get("title", "Untitled").strip()
    context = request.form.get("context", "").strip()

    if "video" not in request.files:
        return jsonify({"error": "No video file"}), 400

    f = request.files["video"]
    if not (f and f.filename and allowed(f.filename, ALLOWED_VIDEO_EXT)):
        return jsonify({"error": "Invalid video format"}), 400

    ext = f.filename.rsplit(".", 1)[1].lower()
    fname = f"film_{uuid.uuid4().hex}.{ext}"
    f.save(UPLOAD_DIR / fname)

    film = {
        "id": uuid.uuid4().hex,
        "title": title,
        "context": context,
        "video_url": f"/uploads/{fname}",
        "notes": [],
        "ai_summary": None,
        "created_at": datetime.utcnow().isoformat(),
    }
    films.append(film)
    save("films", films)
    return jsonify(film), 201


@app.route("/api/films/<film_id>/notes", methods=["POST"])
def add_note(film_id):
    films = load("films", [])
    for film in films:
        if film["id"] == film_id:
            note = {
                "id": uuid.uuid4().hex,
                "timestamp": request.json.get("timestamp", "0:00"),
                "text": request.json.get("text", "").strip(),
                "tag": request.json.get("tag", "general"),  # error, opportunity, win
            }
            film["notes"].append(note)
            save("films", films)
            return jsonify(note), 201
    return jsonify({"error": "Film not found"}), 404


@app.route("/api/films/<film_id>/analyze", methods=["POST"])
def analyze_film(film_id):
    """Send notes to LM Studio for pattern analysis + improvement plan."""
    films = load("films", [])
    film = next((f for f in films if f["id"] == film_id), None)
    if not film:
        return jsonify({"error": "Film not found"}), 404

    if not film["notes"]:
        return jsonify({"error": "Add some notes first — describe what happened at key moments"}), 400

    notes_text = "\n".join(
        f"[{n['timestamp']}] ({n['tag']}) {n['text']}" for n in film["notes"]
    )

    system_prompt = (
        "You are a pickleball coach analyzing a player's self-recorded notes from "
        "a match or practice video. The player is a competitive collegiate athlete. "
        "Identify patterns, name 2-3 specific technical or tactical priorities, and "
        "suggest concrete drills. Be direct and specific. Avoid generic advice."
    )
    user_prompt = (
        f"Match/practice context: {film['context'] or 'Not provided'}\n\n"
        f"Timestamped notes from the player:\n{notes_text}\n\n"
        "Respond with three sections: PATTERNS, PRIORITIES, DRILLS."
    )

    try:
        response = requests.post(
            LM_STUDIO_URL,
            json={
                "model": LM_STUDIO_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.6,
                "max_tokens": 800,
            },
            timeout=120,
        )
        response.raise_for_status()
        summary = response.json()["choices"][0]["message"]["content"]
    except requests.exceptions.ConnectionError:
        return jsonify({
            "error": "Can't reach LM Studio. Make sure LM Studio is running with a model loaded "
                     "and the server is started (default: http://localhost:1234)."
        }), 503
    except Exception as e:
        return jsonify({"error": f"AI request failed: {str(e)}"}), 500

    film["ai_summary"] = {
        "text": summary,
        "generated_at": datetime.utcnow().isoformat(),
    }
    save("films", films)
    return jsonify(film["ai_summary"])


@app.route("/api/films/<film_id>", methods=["DELETE"])
def delete_film(film_id):
    films = load("films", [])
    target = next((f for f in films if f["id"] == film_id), None)
    if target and target.get("video_url"):
        try:
            fname = target["video_url"].split("/")[-1]
            (UPLOAD_DIR / fname).unlink(missing_ok=True)
        except OSError:
            pass
    films = [f for f in films if f["id"] != film_id]
    save("films", films)
    return jsonify({"ok": True})


# ---------- CONTENT CALENDAR API ----------
@app.route("/api/calendar", methods=["GET"])
def get_calendar():
    return jsonify(load("calendar", {"target_date": None, "target_name": "", "posts": []}))


@app.route("/api/calendar/target", methods=["POST"])
def set_target():
    cal = load("calendar", {"target_date": None, "target_name": "", "posts": []})
    cal["target_date"] = request.json.get("target_date")
    cal["target_name"] = request.json.get("target_name", "").strip()
    save("calendar", cal)
    return jsonify(cal)


@app.route("/api/calendar/posts", methods=["POST"])
def add_post():
    cal = load("calendar", {"target_date": None, "target_name": "", "posts": []})
    post = {
        "id": uuid.uuid4().hex,
        "date": request.json.get("date"),
        "platform": request.json.get("platform", "instagram"),  # instagram, tiktok, youtube
        "format": request.json.get("format", "short"),  # short, long, story
        "topic": request.json.get("topic", "").strip(),
        "post_type": request.json.get("post_type", "tip"),  # tip, highlight
        "status": request.json.get("status", "planned"),  # planned, filmed, edited, posted
        "notes": request.json.get("notes", "").strip(),
    }
    cal["posts"].append(post)
    save("calendar", cal)
    return jsonify(post), 201


@app.route("/api/calendar/posts/<post_id>", methods=["PATCH"])
def update_post(post_id):
    cal = load("calendar", {"target_date": None, "target_name": "", "posts": []})
    for p in cal["posts"]:
        if p["id"] == post_id:
            p.update({k: v for k, v in request.json.items() if k != "id"})
            save("calendar", cal)
            return jsonify(p)
    return jsonify({"error": "Post not found"}), 404


@app.route("/api/calendar/posts/<post_id>", methods=["DELETE"])
def delete_post(post_id):
    cal = load("calendar", {"target_date": None, "target_name": "", "posts": []})
    cal["posts"] = [p for p in cal["posts"] if p["id"] != post_id]
    save("calendar", cal)
    return jsonify({"ok": True})


# ---------- ANALYTICS API ----------
@app.route("/api/analytics", methods=["GET"])
def get_analytics():
    return jsonify(load("analytics", []))


@app.route("/api/analytics", methods=["POST"])
def add_analytics():
    entries = load("analytics", [])
    entry = {
        "id": uuid.uuid4().hex,
        "date": request.json.get("date"),
        "platform": request.json.get("platform", "instagram"),
        "format": request.json.get("format", "short"),
        "topic": request.json.get("topic", "").strip(),
        "post_type": request.json.get("post_type", "tip"),
        "views": int(request.json.get("views", 0)),
        "likes": int(request.json.get("likes", 0)),
        "comments": int(request.json.get("comments", 0)),
        "saves": int(request.json.get("saves", 0)),
        "shares": int(request.json.get("shares", 0)),
        "url": request.json.get("url", "").strip(),
        "created_at": datetime.utcnow().isoformat(),
    }
    entries.append(entry)
    save("analytics", entries)
    return jsonify(entry), 201


@app.route("/api/analytics/<entry_id>", methods=["DELETE"])
def delete_analytics(entry_id):
    entries = load("analytics", [])
    entries = [e for e in entries if e["id"] != entry_id]
    save("analytics", entries)
    return jsonify({"ok": True})


@app.route("/api/analytics/insights", methods=["GET"])
def insights():
    """Crunch the numbers to surface what's working."""
    entries = load("analytics", [])
    if not entries:
        return jsonify({"empty": True})

    def avg(key, items):
        nums = [i.get(key, 0) for i in items if isinstance(i.get(key), (int, float))]
        return round(sum(nums) / len(nums), 1) if nums else 0

    def engagement_rate(item):
        views = item.get("views", 0) or 1
        return ((item.get("likes", 0) + item.get("comments", 0) + item.get("saves", 0)) / views) * 100

    # Group by various dimensions
    by_platform = {}
    by_type = {}
    by_format = {}
    for e in entries:
        by_platform.setdefault(e["platform"], []).append(e)
        by_type.setdefault(e["post_type"], []).append(e)
        by_format.setdefault(e["format"], []).append(e)

    top_posts = sorted(entries, key=lambda x: x.get("views", 0), reverse=True)[:5]
    most_engaging = sorted(entries, key=engagement_rate, reverse=True)[:5]

    # Tips vs highlights split
    tip_count = sum(1 for e in entries if e["post_type"] == "tip")
    highlight_count = sum(1 for e in entries if e["post_type"] == "highlight")
    total = tip_count + highlight_count
    actual_split = {
        "tips_pct": round((tip_count / total) * 100, 1) if total else 0,
        "highlights_pct": round((highlight_count / total) * 100, 1) if total else 0,
        "target_tips_pct": 70,
        "target_highlights_pct": 30,
    }

    return jsonify({
        "empty": False,
        "totals": {
            "posts": len(entries),
            "views": sum(e.get("views", 0) for e in entries),
            "likes": sum(e.get("likes", 0) for e in entries),
            "comments": sum(e.get("comments", 0) for e in entries),
            "saves": sum(e.get("saves", 0) for e in entries),
        },
        "by_platform": {
            k: {
                "count": len(v),
                "avg_views": avg("views", v),
                "avg_likes": avg("likes", v),
                "avg_engagement_rate": round(sum(engagement_rate(i) for i in v) / len(v), 2),
            }
            for k, v in by_platform.items()
        },
        "by_post_type": {
            k: {"count": len(v), "avg_views": avg("views", v)}
            for k, v in by_type.items()
        },
        "by_format": {
            k: {"count": len(v), "avg_views": avg("views", v)}
            for k, v in by_format.items()
        },
        "top_views": [
            {"topic": p["topic"], "platform": p["platform"], "views": p.get("views", 0)}
            for p in top_posts
        ],
        "top_engagement": [
            {"topic": p["topic"], "platform": p["platform"], "rate": round(engagement_rate(p), 2)}
            for p in most_engaging
        ],
        "actual_split": actual_split,
    })


# ---------- LM Studio status check ----------
@app.route("/api/ai/status", methods=["GET"])
def ai_status():
    try:
        base = LM_STUDIO_URL.rsplit("/chat/completions", 1)[0]
        r = requests.get(f"{base}/models", timeout=3)
        if r.ok:
            return jsonify({"connected": True, "models": r.json()})
    except requests.exceptions.RequestException:
        pass
    return jsonify({"connected": False})


if __name__ == "__main__":
    print("=" * 60)
    print("  DINKLAB")
    print("=" * 60)
    print(f"  Data dir:    {DATA_DIR}")
    print(f"  Uploads dir: {UPLOAD_DIR}")
    print(f"  LM Studio:   {LM_STUDIO_URL}")
    print(f"  Open:        http://localhost:5000")
    print("=" * 60)
    app.run(host="127.0.0.1", port=5000, debug=True)
