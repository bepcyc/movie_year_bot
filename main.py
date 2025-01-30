import random
import time
import os
import json
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext

# Initialize FastAPI app
app = FastAPI()

# Load Telegram Bot Token from Railway environment variable
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WATCHED_YEARS_FILE = "watched_years.json"

# Initialize Telegram bot application
bot_app = Application.builder().token(TOKEN).build()

# Initialize random seed
random.seed(int(time.time()))

# Decades data
decades = [
    (2010, 2019, 153),
    (2000, 2009, 203),
    (1990, 1999, 259),
    (1980, 1989, 103),
    (1970, 1979, 68),
    (1960, 1969, 59),
    (1950, 1959, 58),
    (1940, 1949, 38),
    (1930, 1939, 23),
    (1929, 1929, 14)
]

# Load watched years from file
def load_watched_years():
    if os.path.exists(WATCHED_YEARS_FILE):
        with open(WATCHED_YEARS_FILE, "r") as f:
            return set(json.load(f))
    return set()

# Save watched years to file
def save_watched_years():
    with open(WATCHED_YEARS_FILE, "w") as f:
        json.dump(list(watched_years), f)

# Initialize watched years
watched_years = load_watched_years()

# Generate weighted list of years
weighted_years = []
for start, end, weight in decades:
    years = list(range(start, end + 1))
    weights = [weight / len(years)] * len(years)
    weighted_years.extend(random.choices(years, weights=weights, k=weight))

def generate_random_year():
    """Generate a random year, avoiding watched years"""
    candidate = random.choice(weighted_years)
    while candidate in watched_years:
        candidate = random.choice(weighted_years)
    return candidate

async def start(update: Update, context: CallbackContext):
    """Start command"""
    await update.message.reply_text("Welcome! Use /random to get a random year.")

async def get_random(update: Update, context: CallbackContext):
    """Send a random year"""
    year = generate_random_year()
    await update.message.reply_text(f"🎲 Random Year: {year}")

async def mark_watched(update: Update, context: CallbackContext):
    """Mark a year as watched"""
    if context.args:
        try:
            year = int(context.args[0])
            watched_years.add(year)
            save_watched_years()
            await update.message.reply_text(f"✅ Marked {year} as watched.")
        except ValueError:
            await update.message.reply_text("⚠️ Please provide a valid year.")
    else:
        await update.message.reply_text("⚠️ Usage: /watched <year>")

# Register handlers
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CommandHandler("random", get_random))
bot_app.add_handler(CommandHandler("watched", mark_watched))

# Webhook route for Telegram updates
@app.post(f"/webhook")
async def webhook(request: Request):
    """Webhook for Telegram"""
    update = Update.de_json(await request.json(), bot_app.bot)
    await bot_app.update_queue.put(update)
    return {"ok": True}
