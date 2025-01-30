import os
import random
import json
from contextlib import asynccontextmanager
from http import HTTPStatus
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response
from telegram import Update
from telegram.ext import Application, ContextTypes, CommandHandler, MessageHandler, filters

# Load environment variables
load_dotenv()
TELEGRAM_BOT_TOKEN: str = os.getenv('TELEGRAM_BOT_TOKEN')
WEBHOOK_DOMAIN: str = os.getenv('RAILWAY_PUBLIC_DOMAIN')

# File to store watched years
WATCHED_YEARS_FILE = "watched_years.json"

# Initialize Telegram bot application
bot_builder = (
    Application.builder()
    .token(TELEGRAM_BOT_TOKEN)
    .updater(None)
    .build()
)

# Decades data for random year generation
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

# Telegram commands
async def start(update: Update, _: ContextTypes.DEFAULT_TYPE):
    """Handles /start command"""
    await update.message.reply_text("Welcome! Use /random to get a random year.")

async def get_random(update: Update, _: ContextTypes.DEFAULT_TYPE):
    """Handles /random command"""
    year = generate_random_year()
    await update.message.reply_text(f"🎲 Random Year: {year}")

async def mark_watched(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /watched <year> command"""
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

# Register commands in bot
bot_builder.add_handler(CommandHandler(command="start", callback=start))
bot_builder.add_handler(CommandHandler(command="random", callback=get_random))
bot_builder.add_handler(CommandHandler(command="watched", callback=mark_watched))

@asynccontextmanager
async def lifespan(_: FastAPI):
    """ Sets the webhook for the Telegram Bot and manages its lifecycle (start/stop). """
    await bot_builder.bot.setWebhook(url=f"{WEBHOOK_DOMAIN}/")
    async with bot_builder:
        await bot_builder.start()
        yield
        await bot_builder.stop()

app = FastAPI(lifespan=lifespan)

@app.post("/")
async def process_update(request: Request):
    """ Handles incoming Telegram updates and processes them with the bot. """
    message = await request.json()
    update = Update.de_json(data=message, bot=bot_builder.bot)
    await bot_builder.process_update(update)
    return Response(status_code=HTTPStatus.OK)
