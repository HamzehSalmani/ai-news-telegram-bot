# 🤖📰 AI News Telegram Agent

[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![Runs on GitHub Actions](https://img.shields.io/badge/runs%20on-GitHub%20Actions-2088FF?logo=github-actions&logoColor=white)](.github/workflows/post-news.yml)
[![LLM via OpenRouter](https://img.shields.io/badge/LLM-OpenRouter-7C3AED)](https://openrouter.ai)

A fully serverless agent that automatically fetches the latest AI news, ranks the most *useful* stories with an LLM, summarizes them in friendly, conversational Persian (bullet points), and posts each one — **with an image and a source link** — to a Telegram channel.

No server required. It runs entirely on **GitHub Actions** on a schedule.

---

## ✨ Features
- **Curated, not noisy** — an LLM selector keeps only practical news (new models, new capabilities, new tools/APIs, notable technical releases) and drops political/financial/event noise.
- **Conversational Persian summaries** — short, friendly bullet points, as if a friend were telling you the news.
- **Auto image extraction** — pulls the article's `og:image` / `twitter:image`.
- **No duplicates** — a SQLite database (`posted.db`) tracks posted URLs by hash.
- **Resilient** — any single network/parse error is logged and skipped; one bad item never breaks the run.
- **Zero infrastructure** — scheduled GitHub Actions runner, secrets stored as GitHub Secrets.

---

## 🏗️ Architecture

```
                ┌──────────────────── GitHub Actions (cron) ────────────────────┐
                │                                                                │
  RSS feeds ──▶ │  fetcher  ──▶  dedup  ──▶  selector (LLM)  ──▶  summarizer (LLM) │ ──▶ Telegram
 (OpenAI,       │   feeds.py    dedup.py      selector.py          summarizer.py   │      channel
  DeepMind,     │      │                          │ picks most         │ Persian   │   (sendPhoto)
  HF, TechCrunch│      ▼                          ▼ useful             ▼ bullets    │
  …)            │  image_extractor.py (og:image)            telegram_poster.py     │
                │                                                                │
                │  posted.db is committed back to the repo after each run ───────┘
                └────────────────────────────────────────────────────────────────┘
```

Because the runner is stateless, `posted.db` is **committed back to the repository** after every run (the *Persist dedup database* step) so duplicates are avoided across runs.

> **Why GitHub Actions?** The original deployment target was filtered for both Telegram and the LLM API. GitHub's runners live outside that network, which removed the access problem entirely — and made the whole thing free and serverless.

---

## 🧩 Project structure
| File | Role |
|------|------|
| `main.py` | Orchestration: fetch → dedup → **select most useful** → image + summary → post → record |
| `selector.py` | LLM-based ranking of the most useful new stories (keyword filter + LLM scoring) |
| `fetcher.py` | RSS parsing with `feedparser` (+ optional web search); `@dataclass Article` |
| `feeds.py` | The list of RSS feeds |
| `image_extractor.py` | Extracts `og:image` / `twitter:image` via `requests` + BeautifulSoup |
| `summarizer.py` | Persian summarization via OpenRouter; structured JSON output |
| `telegram_poster.py` | Builds the HTML message and sends it to Telegram (handles HTTP 429) |
| `dedup.py` | SQLite (`posted.db`): prevents re-posting via URL hashes |
| `config.py` | Reads env vars (with `python-dotenv` for local runs) + defaults |

---

## 🚀 Setup (deploy your own)

### 1. Create a Telegram bot
1. Message [@BotFather](https://t.me/BotFather), send `/newbot`, pick a name + username.
2. Copy the **token** it gives you (this is `TELEGRAM_BOT_TOKEN`).
3. Add the bot to your channel as an **admin** with **Post Messages** permission.
4. Get your channel ID: a public channel is `@your_channel`; for a private channel use the numeric id (e.g. `-1001234567890`).

### 2. Get an OpenRouter key
Create a key at [openrouter.ai/keys](https://openrouter.ai/keys). The default model `google/gemini-2.5-flash` is cheap and good at Persian.

### 3. Add GitHub Secrets
In your fork: **Settings → Secrets and variables → Actions → New repository secret**. Add:

| Secret | Example | Notes |
|--------|---------|-------|
| `TELEGRAM_BOT_TOKEN` | `123456:ABC-…` | from BotFather |
| `TELEGRAM_CHANNEL_ID` | `-1001234567890` | numeric id or `@username` |
| `OPENROUTER_API_KEY` | `sk-or-v1-…` | from OpenRouter |
| `OPENROUTER_MODEL` | `google/gemini-2.5-flash` | any OpenRouter model |
| `MAX_POSTS_PER_RUN` | `1` | posts per run |
| `ENABLE_WEB_SEARCH` | `false` | appends `:online` to the model (extra cost) |

### 4. Schedule
The workflow [`.github/workflows/post-news.yml`](.github/workflows/post-news.yml) runs on cron:

```yaml
schedule:
  - cron: "30 5,10,15 * * *"   # 09:00, 14:00, 19:00 Iran time (UTC+3:30)
```

Trigger a manual test run from the **Actions** tab, or with the CLI:

```bash
gh workflow run post-news.yml
```

---

## 💻 Running locally
```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your values
python main.py
```

Config variables (see [`.env.example`](.env.example)):

| Variable | Description | Default |
|----------|-------------|---------|
| `MAX_POSTS_PER_RUN` | Max stories per run | `3` |
| `OPENROUTER_MODEL` | OpenRouter model id | `google/gemini-2.5-flash` |
| `ENABLE_WEB_SEARCH` | Optional web search (`:online`, extra cost) | `false` |

To add or remove news sources, edit [`feeds.py`](feeds.py).

---

## 🛠️ Tech stack
Python 3.11 · OpenRouter (OpenAI-compatible SDK) · feedparser · BeautifulSoup · SQLite · Telegram Bot API · GitHub Actions

## 📝 License
Personal project — feel free to fork and adapt.
