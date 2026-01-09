from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import requests
import os

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("❌ BOT_TOKEN topilmadi. Railway Variables ni tekshiring.")

alerts = {}

def get_price(coin_id: str):
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": coin_id, "vs_currencies": "usd"}
    r = requests.get(url, params=params, timeout=10)
    data = r.json()
    if coin_id not in data:
        return None
    return data[coin_id]["usd"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Salom!\n\n"
        "Buyruqlar:\n"
        "/price bitcoin\n"
        "/set bitcoin 90000\n"
        "/alerts\n\n"
        "🪙 Har qanday coin (CoinGecko ID bilan)"
    )

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("❌ Masalan: /price bitcoin")
        return

    coin = context.args[0].lower()
    price = get_price(coin)

    if price is None:
        await update.message.reply_text("❌ Coin topilmadi")
        return

    await update.message.reply_text(f"💰 {coin.upper()} narxi: ${price}")

async def set_alert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text("❌ Masalan: /set bitcoin 90000")
        return

    coin = context.args[0].lower()

    try:
        target = float(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Narx raqam bo‘lishi kerak")
        return

    if get_price(coin) is None:
        await update.message.reply_text("❌ Coin topilmadi")
        return

    chat_id = update.effective_chat.id
    alerts.setdefault(chat_id, {})[coin] = target

    await update.message.reply_text(f"✅ Alert qo‘yildi: {coin.upper()} ≥ ${target}")

async def show_alerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in alerts or not alerts[chat_id]:
        await update.message.reply_text("📭 Aktiv alertlar yo‘q")
        return

    text = "📌 Aktiv alertlar:\n"
    for coin, price in alerts[chat_id].items():
        text += f"- {coin.upper()} ≥ ${price}\n"

    await update.message.reply_text(text)

async def alert_checker(context: ContextTypes.DEFAULT_TYPE):
    for chat_id, user_alerts in list(alerts.items()):
        for coin, target in list(user_alerts.items()):
            price = get_price(coin)
            if price and price >= target:
                await context.bot.send_message(
                    chat_id,
                    f"🚨 ALERT!\n{coin.upper()} = ${price}"
                )
                del alerts[chat_id][coin]

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("price", price))
app.add_handler(CommandHandler("set", set_alert))
app.add_handler(CommandHandler("alerts", show_alerts))

app.job_queue.run_repeating(alert_checker, interval=30, first=10)

app.run_polling()
