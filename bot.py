"""
Telegram → Google Calendar Bot
Parses natural language event messages and creates Google Calendar events
with invites for all family/group members.
"""

import logging
import os
import json
from datetime import datetime, timezone

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

from parser import parse_event_with_gemini
from calendar_client import create_calendar_event

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hi! I'm your family calendar bot.\n\n"
        "Just send me an event in any format, for example:\n"
        "• *dentist 23 May 2026, at 14:45*\n"
        "• *4.12.26, 9am doctor for kid*\n"
        "• *bring fruits to the kita, 30 of June*\n\n"
        "I'll parse it and add it to the shared Google Calendar with invites for everyone! 📅",
        parse_mode="Markdown"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *How to use:*\n\n"
        "Just send any message describing an event. I understand:\n"
        "• Dates in any format (23 May, 23.05, 05/23, next Monday…)\n"
        "• Times (14:45, 2pm, 9am, noon…)\n"
        "• Locations (optional)\n"
        "• Any description\n\n"
        "I'll confirm what I understood before creating the event.\n\n"
        "*Commands:*\n"
        "/start — welcome message\n"
        "/help — this message",
        parse_mode="Markdown"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw_text = update.message.text
    user = update.message.from_user.first_name
    logger.info(f"Message from {user}: {raw_text}")

    # Send "thinking" indicator
    processing_msg = await update.message.reply_text("⏳ Parsing your event...")

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Step 1: Parse with Gemini
    event_data, error = await parse_event_with_gemini(raw_text, today)

    if error or not event_data:
        await processing_msg.edit_text(
            f"❌ Sorry, I couldn't understand that as an event.\n\n"
            f"Try something like: *dentist 23 May at 14:00* or *meeting tomorrow 3pm*",
            parse_mode="Markdown"
        )
        return

    # Step 2: Create Google Calendar event
    event_link, cal_error = create_calendar_event(event_data)

    if cal_error:
        await processing_msg.edit_text(
            f"⚠️ I parsed the event but couldn't add it to Google Calendar:\n`{cal_error}`",
            parse_mode="Markdown"
        )
        return

    # Step 3: Confirm to user
    date_str = event_data.get("date", "unknown date")
    time_str = event_data.get("time", "")
    title = event_data.get("title", "Event")
    location = event_data.get("location", "")

    time_display = f" at {time_str}" if time_str else ""
    location_display = f"\n📍 {location}" if location else ""

    await processing_msg.edit_text(
        f"✅ *Event created!*\n\n"
        f"📌 *{title}*\n"
        f"📅 {date_str}{time_display}"
        f"{location_display}\n\n"
        f"👥 Added to shared calendar for all members!\n"
        f"[View in Google Calendar]({event_link})",
        parse_mode="Markdown",
        disable_web_page_preview=True
    )


def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot started! Polling for messages...")
    app.run_polling()


if __name__ == "__main__":
    main()
