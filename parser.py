"""
Event parser using Google Gemini Flash API.
Converts messy natural language into structured event data.
"""

import os
import json
import logging
import asyncio
import aiohttp

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1/models/"
    "gemini-1.5-flash:generateContent"
)


SYSTEM_PROMPT = """You are an event parser. Extract calendar event details from natural language messages.

Always respond with ONLY valid JSON, no markdown, no explanation.

Output format:
{
  "title": "short event title",
  "date": "YYYY-MM-DD",
  "time": "HH:MM",
  "end_time": "HH:MM",
  "location": "location string or null",
  "description": "fuller description or null",
  "is_all_day": false
}

Rules:
- If no year specified, assume the next upcoming occurrence of that date
- If no time specified, set is_all_day to true and time to null
- Default event duration is 1 hour unless stated otherwise
- If the message is NOT an event at all, return: {"error": "not an event"}
- Keep titles short and clear (e.g. "Dentist appointment", "Doctor for kid", "Kita - bring fruits")
- For ambiguous dates like "30 of June" assume current or next year
"""


async def parse_event_with_gemini(raw_text: str, today: str) -> tuple[dict | None, str | None]:
    """
    Parse a natural language event message using Gemini Flash.
    Returns (event_data, error_message).
    """

    user_prompt = f"{SYSTEM_PROMPT}\n\nToday is {today}. Parse this event: {raw_text}"

    payload = {
        "contents": [
            {"parts": [{"text": user_prompt}]}
        ],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 300,
        }
    }

    headers = {"Content-Type": "application/json"}
    url = f"{GEMINI_URL}?key={GEMINI_API_KEY}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    logger.error(f"Gemini API error {resp.status}: {text}")
                    return None, f"Gemini API error: {resp.status}"

                data = await resp.json()

        # Extract text from Gemini response
        raw_json = data["candidates"][0]["content"]["parts"][0]["text"].strip()

        # Strip markdown code fences if present
        if raw_json.startswith("```"):
            raw_json = raw_json.split("```")[1]
            if raw_json.startswith("json"):
                raw_json = raw_json[4:]
            raw_json = raw_json.strip()

        event = json.loads(raw_json)

        if "error" in event:
            logger.info(f"Gemini: not an event — {raw_text!r}")
            return None, "not_an_event"

        logger.info(f"Parsed event: {event}")
        return event, None

    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e} | raw: {raw_json!r}")
        return None, "Failed to parse Gemini response as JSON"

    except Exception as e:
        logger.error(f"Gemini request failed: {e}")
        return None, str(e)
