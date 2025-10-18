# bot.py
# استفاده: مقدار TOKEN و ADMIN_ID رو جایگزین کن
# اجرا: python bot.py
# نیازمندی‌ها: python-telegram-bot, pandas, openpyxl

import json
import os
import pandas as pd
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# ====== تنظیمات ======
TOKEN = "8334315941:AAGAvLGJlTx-7eGTRfX2xOz3MyMGrvYe5OY"
ADMINS = [1574915126, 1369043494]  # آی‌دی عددی ادمین
DATA_FILE = "data/scores.json"
UPLOAD_PATH = "uploaded.xlsx"  # مسیر موقت دریافت فایل

# --- تابع شروع ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! لطفا کد دانشجویی خود را ارسال کنید.")


# --- تابع دریافت فایل اکسل از ادمین ---
async def handle_excel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in ADMINS:
        await update.message.reply_text("فقط ادمین اجازه ارسال فایل دارد.")
        return

    document = update.message.document
    if not document.file_name.endswith(('.xls', '.xlsx')):
        await update.message.reply_text("فقط فایل Excel مجازه (xls یا xlsx).")
        return

    file = await document.get_file()
    path = "uploaded.xlsx"
    await file.download_to_drive(path)

    df = pd.read_excel(path)
    if df.shape[1] < 2:
        await update.message.reply_text("فایل باید حداقل دو ستون (کد دانشجویی و نمره) داشته باشد.")
        return

    scores = dict(zip(df.iloc[:, 0].astype(str), df.iloc[:, 1].astype(str)))
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(scores, f, ensure_ascii=False, indent=2)

    await update.message.reply_text("✅ فایل با موفقیت ذخیره شد!")


# --- تابع دریافت پیام از دانشجو ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            scores = json.load(f)
    except FileNotFoundError:
        await update.message.reply_text("هیچ داده‌ای موجود نیست. لطفاً منتظر آپلود فایل باشید.")
        return

    if code in scores:
        await update.message.reply_text(f"🎓 نمره شما: {scores[code]}")
    else:
        await update.message.reply_text("❌ کد دانشجویی پیدا نشد.")


# --- تابع مخصوص ادمین‌ها برای مشاهده نمرات ---
async def show_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in ADMINS:
        await update.message.reply_text("شما ادمین نیستید.")
        return

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            scores = json.load(f)
    except FileNotFoundError:
        await update.message.reply_text("هیچ داده‌ای ذخیره نشده.")
        return

    text = "\n".join([f"{k}: {v}" for k, v in scores.items()])
    if len(text) > 4000:
        await update.message.reply_text("📊 فایل نمرات طولانیه. خلاصه‌ای نمایش داده می‌شود:")
        text = "\n".join(list(scores.items())[:50])  # فقط ۵۰ مورد اول
    await update.message.reply_text(f"📊 لیست نمرات:\n\n{text}")


if __name__ == "__main__":
    from telegram.ext import ApplicationBuilder

    app = ApplicationBuilder().token(TOKEN).build()

    # اضافه کردن هاندلرها
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("all", show_all))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_excel))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    app.run_polling()  # ← مستقیم اینو صدا بزن
