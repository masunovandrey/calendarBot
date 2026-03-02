# 📅 Telegram → Google Calendar Bot

A family/group bot that reads natural language event messages from Telegram and automatically creates Google Calendar events with invites for all members.

## ✨ Examples

Send any of these to the bot and it creates the calendar event:

```
dentist 23 May 2026, at 14:45
4.12.26, 9am doctor for kid
bring fruits to the kita, 30 of June
meeting tomorrow at 3pm
```

---

## 🗂 Project Structure

```
calbot/
├── bot.py              # Telegram bot — entry point
├── parser.py           # Gemini AI event parser
├── calendar_client.py  # Google Calendar API client
├── requirements.txt    # Python dependencies
├── railway.toml        # Railway deployment config
├── .env.example        # Environment variable template
└── README.md
```

---

## 🚀 Setup Guide

### Step 1 — Create a Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot`
3. Choose a name (e.g. `Family Calendar`) and username (e.g. `family_cal_bot`)
4. Copy the **bot token** — you'll need it as `TELEGRAM_TOKEN`

---

### Step 2 — Get a Free Gemini API Key

1. Go to **https://aistudio.google.com/app/apikey**
2. Click **Create API Key**
3. Copy it — you'll need it as `GEMINI_API_KEY`

Free tier: 15 requests/minute, 1M tokens/day — plenty for a small group.

---

### Step 3 — Set Up Google Calendar API

This is the most involved step, but only takes ~10 minutes.

#### 3a. Create a Google Cloud Project

1. Go to **https://console.cloud.google.com**
2. Click the project dropdown → **New Project**
3. Name it `calbot` or anything you like → **Create**

#### 3b. Enable the Google Calendar API

1. In your project, go to **APIs & Services → Library**
2. Search for **Google Calendar API**
3. Click **Enable**

#### 3c. Create a Service Account

1. Go to **APIs & Services → Credentials**
2. Click **Create Credentials → Service Account**
3. Name it `calbot-service` → **Create and Continue** → **Done**
4. Click on the service account you just created
5. Go to the **Keys** tab → **Add Key → Create new key → JSON**
6. A `.json` file downloads — **keep this safe!**

#### 3d. Share Your Calendar with the Service Account

1. Open **Google Calendar** (calendar.google.com)
2. Find the calendar you want to use (or create a new shared one)
3. Click the three dots → **Settings and sharing**
4. Under **Share with specific people**, click **Add people**
5. Enter the service account email (looks like `calbot-service@your-project.iam.gserviceaccount.com`)
6. Set permission to **Make changes to events**
7. Copy the **Calendar ID** from "Integrate calendar" section (for primary calendar, just use `primary`)

#### 3e. Prepare the Service Account JSON

Open the downloaded `.json` file, copy its **entire contents** as a single line.
You'll paste this as the `GOOGLE_SERVICE_ACCOUNT_JSON` environment variable.

---

### Step 4 — Deploy to Railway (Free)

1. Push this project to a **GitHub repository**

2. Go to **https://railway.app** and sign up (free, no credit card)

3. Click **New Project → Deploy from GitHub repo**

4. Select your repository

5. Go to **Variables** tab and add these environment variables:

| Variable | Value |
|---|---|
| `TELEGRAM_TOKEN` | From Step 1 |
| `GEMINI_API_KEY` | From Step 2 |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Full JSON content from Step 3d |
| `CALENDAR_ID` | `primary` or your calendar ID |
| `MEMBER_EMAILS` | `alice@gmail.com,bob@gmail.com` |
| `TIMEZONE` | e.g. `Europe/Berlin` |

6. Click **Deploy** — your bot will be live in ~2 minutes!

---

### Step 5 — Test It!

Open Telegram, find your bot, and send:
```
dentist 23 May at 14:00
```

You should get a confirmation message with a link to the calendar event, and all members receive an email invite.

---

## 🔧 Local Development

```bash
# Clone and install dependencies
pip install -r requirements.txt

# Copy and fill in your environment variables
cp .env.example .env
# Edit .env with your real values

# Run locally
python bot.py
```

> For local development, install `python-dotenv` and add `from dotenv import load_dotenv; load_dotenv()` at the top of `bot.py`.

---

## 🛠 Troubleshooting

**Bot doesn't respond**
- Check Railway logs for errors
- Make sure `TELEGRAM_TOKEN` is correct

**"Gemini API error"**
- Verify `GEMINI_API_KEY` is valid at aistudio.google.com

**"Google Calendar error"**
- Make sure the service account has been shared on the calendar (Step 3d)
- Verify `GOOGLE_SERVICE_ACCOUNT_JSON` is valid JSON (no line breaks)

**Events created but no invites**
- Check that `MEMBER_EMAILS` are correct and comma-separated
- Gmail sometimes puts calendar invites in Spam on first use

---

## 📋 Environment Variables Reference

| Variable | Required | Description |
|---|---|---|
| `TELEGRAM_TOKEN` | ✅ | Telegram bot token from @BotFather |
| `GEMINI_API_KEY` | ✅ | Google Gemini API key |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | ✅ | Full service account JSON as string |
| `MEMBER_EMAILS` | ✅ | Comma-separated invite emails |
| `CALENDAR_ID` | ✅ | `primary` or specific calendar ID |
| `TIMEZONE` | ✅ | IANA timezone e.g. `Europe/Berlin` |
