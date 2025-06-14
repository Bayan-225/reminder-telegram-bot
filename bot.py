import json
import os
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from telegram import Update
from telegram import ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

REMINDER_FILE = "reminders.json"

def load_reminders():
    if not os.path.exists(REMINDER_FILE):
        return {}
    with open(REMINDER_FILE, "r") as f:
        return json.load(f)

def save_reminders(data):
    with open(REMINDER_FILE, "w") as f:
        json.dump(data, f, indent=2)

reminders = load_reminders()

async def check_reminders(app):
    now = datetime.now().strftime("%H:%M")
    for user_id, user_reminders in reminders.items():
        to_remove = []
        for item in user_reminders:
            if item["time"] == now:
                try:
                    await app.bot.send_message(chat_id=user_id, text=f"🔔 Напоминание: {item['text']}")
                    to_remove.append(item)
                except Exception as e:
                    print(f"Ошибка отправки: {e}")
        if to_remove:
            for item in to_remove:
                user_reminders.remove(item)
            save_reminders(reminders)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["/help"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Привет! Я бот-напоминалка.\nИспользуй /add <текст> <время>, например:\n/add выпить чай 16:30",
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("/add ТЕКСТ ВРЕМЯ — добавить напоминание\n/list — показать активные\n/clear — удалить все")

async def add_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        args = context.args
        if len(args) < 2:
            return await update.message.reply_text("❗ Пример: /add позвонить другу 18:30")
        text = " ".join(args[:-1])
        time = args[-1]
        datetime.strptime(time, "%H:%M")  

        user_id = str(update.effective_user.id)
        if user_id not in reminders:
            reminders[user_id] = []
        reminders[user_id].append({"text": text, "time": time})
        save_reminders(reminders)

        await update.message.reply_text(f"✅ Напоминание добавлено: \"{text}\" в {time}")
    except ValueError:
        await update.message.reply_text("❌ Время должно быть в формате ЧЧ:ММ (например, 18:45)")

async def list_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_reminders = reminders.get(user_id, [])
    if not user_reminders:
        return await update.message.reply_text("У тебя нет активных напоминаний.")
    text = "📝 Твои напоминания:\n" + "\n".join([f"• {r['text']} в {r['time']}" for r in user_reminders])
    await update.message.reply_text(text)

async def clear_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    reminders[user_id] = []
    save_reminders(reminders)
    await update.message.reply_text("🗑 Все напоминания удалены.")

import asyncio

async def main():
    TOKEN = "8093711785:AAFq2DMhTBoSz_C7yFerKa2QuRuoUFmYm_0"
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("add", add_reminder))
    app.add_handler(CommandHandler("list", list_reminders))
    app.add_handler(CommandHandler("clear", clear_reminders))

    loop = asyncio.get_running_loop()
    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: asyncio.run_coroutine_threadsafe(check_reminders(app), loop), "interval", minutes=1)
    scheduler.start()

    print("🤖 Бот запущен...")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    import nest_asyncio

    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())

