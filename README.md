# DinkLab ◆

A self-hosted desktop app for competitive pickleball players who also create content. Track your gear, break down your film with local AI, plan your content calendar, and find out what's actually working — all running on your own machine, no cloud, no subscriptions.

Built by Aryan Mozar as a personal tool and a portfolio project demonstrating full-stack Python development with a packaged desktop UI and local LLM integration.

![Platform: Windows · macOS](https://img.shields.io/badge/platform-windows%20%7C%20macos-blue) ![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue) ![License: MIT](https://img.shields.io/badge/license-MIT-green)

---

## Features

### 01 — The Bag
A visual catalog of your loadout. Paddles, shoes, bags, apparel, accessories — log specs, notes, when you started using each piece, and a photo.

### 02 — Film Room
Upload match or practice footage and watch it in the app. Drop timestamped notes tagged as **errors**, **opportunities**, **wins**, or **general**. Hit *Generate AI Breakdown* and a locally-hosted LLM reads your notes and returns:
- **Patterns** it sees across your notes
- **Priorities** — two or three specific things to work on
- **Drills** — concrete practice ideas

Because the AI reads *your* observations, you get genuinely personal feedback without sending anything to the cloud.

### 03 — Content Calendar
Lock in a target event, get a live day-countdown, and plan posts across Instagram / TikTok / YouTube. Each post has a status (planned → filmed → edited → posted) and a type (tip or highlight) so you can keep the planned mix honest against the 70/30 target.

### 04 — Analytics
Log post performance (views, likes, comments, saves, shares) and let the dashboard surface totals, top performers, engagement rates, by-platform breakdowns, and your **actual** tips-vs-highlights split vs. the target.

Connect YouTube and Instagram to pull data automatically — no manual entry needed. TikTok is manual-entry (their API is not open to individual creators).

---

## Quick start (run from source)

This works the same on Windows and macOS.

```bash
git clone https://github.com/AryanMozar/dinklab.git
cd dinklab
python -m venv venv

# Windows
venv\Scripts\activate

# macOS
source venv/bin/activate

pip install -r requirements.txt
python launcher.py
```

The DinkLab window opens. Done.

---

## Build a standalone app (no Python install needed by the end user)

Want a real double-clickable app you can pin to your taskbar / dock? One command:

```bash
python build.py
```

**Output:**
- **Windows** → `dist/DinkLab/DinkLab.exe` — the whole `DinkLab` folder is portable, you can zip it, put a shortcut on your desktop, or move it anywhere.
- **macOS** → `dist/DinkLab.app` — drag into `/Applications` to install.

**Important:** PyInstaller can only build for the OS it's running on. To get both:
- Build the `.exe` on a Windows machine
- Build the `.app` on a Mac

You only need to do this once when you want a real shippable app. For day-to-day development, just use `python launcher.py`.

---

## Social media integration setup

YouTube and Instagram can auto-sync your post analytics into the Analytics tab. Setup takes ~5 minutes per platform and only needs to be done once.

### YouTube (Google Cloud Console)

1. Go to [console.cloud.google.com](https://console.cloud.google.com) and create a new project (e.g. "DinkLab").
2. Enable the **YouTube Data API v3**: *APIs & Services → Library → search "YouTube Data API v3" → Enable*.
3. Create OAuth credentials: *APIs & Services → Credentials → Create Credentials → OAuth client ID*.
   - Application type: **Desktop app**
   - Name: anything (e.g. "DinkLab desktop")
4. Download the credentials JSON and note the **Client ID** and **Client Secret**.
5. Under *OAuth consent screen*, add your Google account email as a test user (required while the app is in "Testing" mode).
6. In DinkLab → Analytics, click **Connect YouTube**, enter your Client ID and Client Secret, then click **Start OAuth**. Your browser will open to Google's sign-in — authorize it and you'll be redirected back automatically.

**Redirect URI** (pre-registered by default for desktop apps; no action needed):
`http://localhost:5000/api/integrations/youtube/callback`

### Instagram (Facebook Developer)

1. Go to [developers.facebook.com](https://developers.facebook.com) and create an app: *My Apps → Create App → Other → Consumer*.
2. Add the **Instagram Basic Display** product to your app.
3. Under *Instagram Basic Display → Basic Display*:
   - Add a **Valid OAuth Redirect URI**: `http://localhost:5000/api/integrations/instagram/callback`
   - Add your Instagram account as a test user under *Roles → Test Users*
4. Copy your **Instagram App ID** and **Instagram App Secret** from the *Basic Display* settings page.
5. In DinkLab → Analytics, click **Connect Instagram**, enter the App ID and App Secret, then click **Start OAuth**.

> **Note:** Instagram long-lived tokens last 60 days. DinkLab refreshes the token automatically every time you sync, so as long as you sync at least once every two months the connection stays live.

---

## LM Studio setup (for the Film Room AI)

The Film Room AI breakdown needs a local LLM. Everything else works without it.

1. Download [LM Studio](https://lmstudio.ai/) (free, Windows + macOS)
2. Inside the app, search for and download a model — anything ~7B–13B is great. Recommended starters:
   - **Llama 3.1 8B Instruct** (balanced)
   - **Mistral 7B Instruct** (faster on lower-end hardware)
3. Open the **Local Server** tab, load the model, and click **Start Server**. Defaults to `http://localhost:1234`.

The AI status dot in the top right of DinkLab goes green when it can reach LM Studio.

To override the URL or model:

```bash
# Windows (PowerShell)
$env:LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"

# macOS / Linux
export LM_STUDIO_URL="http://localhost:1234/v1/chat/completions"
```

---

## Where your data lives

When running from source, data is stored in the project's `data/` and `uploads/` folders.

When running as a packaged app, your data lives in a user folder that survives reinstalls:

- **Windows:** `%APPDATA%\DinkLab\`
- **macOS:** `~/Library/Application Support/DinkLab/`

Nothing leaves your machine. No cloud, no telemetry.

---

## Stack

- **Backend:** Python 3.10+, Flask
- **Desktop wrapper:** pywebview (native OS webview, no Chromium bundled)
- **Frontend:** Vanilla HTML / CSS / JS — no build step, no npm
- **Storage:** Local JSON files and local file uploads
- **AI:** [LM Studio](https://lmstudio.ai/) running a local model via its OpenAI-compatible API
- **Packaging:** PyInstaller (one-file spec, cross-platform)

No accounts, no database server, no cloud APIs, no monthly fees.

---

## Project structure

```
dinklab/
├── launcher.py             # Desktop app entry point
├── build.py                # One-command build script
├── dinklab.spec            # PyInstaller config
├── backend/
│   └── app.py              # Flask app — all API routes and storage
├── frontend/
│   ├── templates/
│   │   └── index.html      # Single-page UI
│   └── static/
│       ├── style.css       # Theming and layout
│       └── app.js          # All client logic
├── requirements.txt
└── README.md
```

---

## How the AI breakdown actually works

Real talk, because the alternative (computer vision analyzing your gameplay) is genuinely hard and not free. Here's what DinkLab does instead:

1. You watch your own film in the app
2. You drop timestamped notes as you go — *"2:14 — late on backhand drive"*, *"5:33 — great third-shot drop"*
3. The notes get sent to your local LLM with a coaching-focused system prompt
4. The LLM looks for patterns across your notes and outputs structured feedback

You're the eyes; the AI is the pattern-finder. It works because your notes are signal, not noise — you're already focused on what matters. Everything runs locally, so your footage and notes never leave your machine.

---

## Roadmap

- [x] Custom app icon (Windows `.ico` + macOS `.icns`)
- [x] YouTube + Instagram analytics auto-sync
- [ ] Export gear list as a shareable image
- [ ] Calendar export to `.ics` for Apple/Google Calendar
- [ ] Tag-based filtering on film notes
- [ ] Multi-session AI analysis
- [ ] CSV import for analytics
- [ ] Auto-update mechanism

---

## Why I built this

I play competitively for JMU's club team and I'm building a content channel around collegiate pickleball with a teammate. Existing tools either cost money, live in someone else's cloud, or don't fit the workflow. This one does what I actually need, runs locally, and ships as one repo.

It also doubles as a portfolio piece showing Flask, file upload handling, local LLM integration, JSON persistence, frontend without build tools, native desktop packaging, and cross-platform builds.

---

## License

MIT — do whatever you want with it.
