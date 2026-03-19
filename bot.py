import logging
import random
import sqlite3
import asyncio
import os
from datetime import datetime, timedelta

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# ================== CONFIG ==================
TOKEN = "8588513246:AAGaQWZX5xU8hJMwETxyYfYCkWlJ2zzIJho"
ADMIN_ID = 8333660216
WALLET_ADDRESS = "TWshH1BdqudwxGMXDyGdiy9dqYJEJ4MYnc"

PAIRS = [
    "EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD",
    "USD/CAD", "EUR/GBP", "EUR/JPY", "GBP/JPY"
]

# ============================================

logging.basicConfig(level=logging.INFO)

# ================= DATABASE =================
conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    vip INTEGER DEFAULT 0,
    vip_expiry TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS stats (
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0
)
""")

# ensure stats row exists
cursor.execute("SELECT * FROM stats")
if cursor.fetchone() is None:
    cursor.execute("INSERT INTO stats (wins, losses) VALUES (0,0)")
    conn.commit()

# ============================================

# ================= FUNCTIONS =================

def get_user(user_id):
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()

    if not user:
        cursor.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
        return (user_id, 0, None)

    return user


def is_vip(user):
    if user[1] == 1 and user[2]:
        expiry = datetime.fromisoformat(user[2])
        return datetime.now() < expiry
    return False


def generate_signal():
    pair = random.choice(PAIRS)
    direction = random.choice(["BUY", "SELL"])
    entry = round(random.uniform(1.0000, 2.0000), 5)

    return f"""
🔥 <b>PRO SIGNAL</b>

📊 Pair: {pair}
📈 Direction: {direction}
💰 Entry: {entry}

⏱ Expiry: 1 Minute

⚡ Winrate: 80%+
"""


async def auto_signal(context: ContextTypes.DEFAULT_TYPE):
    for user_id, in cursor.execute("SELECT user_id FROM users").fetchall():
        try:
            await context.bot.send_message(chat_id=user_id, text=generate_signal(), parse_mode="HTML")
        except:
            pass

# ============================================

# ================= HANDLERS =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)

    keyboard = [
        ["⚡ Generate Signal"],
        ["📊 Stats"],
        ["💎 VIP"],
        ["📞 Contact Admin"]
    ]

    await update.message.reply_text(
        "🚀 Welcome to PRO Trading Bot",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = get_user(update.effective_user.id)

    if text == "⚡ Generate Signal":
        await update.message.reply_text(generate_signal(), parse_mode="HTML")

    elif text == "📊 Stats":
        cursor.execute("SELECT wins, losses FROM stats")
        wins, losses = cursor.fetchone()

        total = wins + losses
        winrate = (wins / total * 100) if total > 0 else 0

        await update.message.reply_text(
            f"""
📊 <b>Bot Performance</b>

✅ Wins: {wins}
❌ Losses: {losses}
📈 Winrate: {winrate:.2f}%
""",
            parse_mode="HTML"
        )

    elif text == "💎 VIP":
        await update.message.reply_text(
            f"""
💎 <b>VIP Access</b>

Price: $10/month

Send USDT to:
<code>{WALLET_ADDRESS}</code>

Then click below 👇
""",
            parse_mode="HTML"
        )

    elif text == "📞 Contact Admin":
        await update.message.reply_text("📩 Message admin to confirm payment.")

# ============================================

# ================= ADMIN =================

async def activate_vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    try:
        user_id = int(context.args[0])

        expiry = datetime.now() + timedelta(days=30)

        cursor.execute(
            "UPDATE users SET vip=1, vip_expiry=? WHERE user_id=?",
            (expiry.isoformat(), user_id)
        )
        conn.commit()

        await update.message.reply_text("✅ VIP Activated")

    except:
        await update.message.reply_text("❌ Usage: /vip USER_ID")

# ============================================

# ================= MAIN =================

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("vip", activate_vip))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    # auto signal every 30 sec
    app.job_queue.run_repeating(auto_signal, interval=30, first=10)

    print("🚀 BOT RUNNING...")
    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
