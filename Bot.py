# bot_timer.py
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
import os

# === إعداد السجل (logging) ===
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# === الضبط ===
TOKEN = os.getenv("8111881788:AAGnWrxvSKVe65g2yaSNDH3ggxdAFFjZtqQ") or "ضع_هنا_توكن_البوت_إلا_ماستعملتش_ENV"

# نخزنو التايمرات حسب user_id باش نلغيوها إلا ضغط الزر
user_jobs = {}

# رابط اللي نبغي نبعثه إلا ضغط الزر
LINK_ON_PRESS = "https://www.google.com"
# رابط اللي نبغي نبعثه إلا ما تضغطش خلال 5 دقائق
LINK_ON_TIMEOUT = "https://www.instagram.com"
# مدة الانتظار بالثواني (5 دقائق = 300 ث)
TIMEOUT_SECONDS = 5 * 60


def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    # زر اللي المستخدم يضغط عليه
    keyboard = [
        [InlineKeyboardButton("اضغط هنا باش تشوف الرابط", callback_data="press_show_link")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # ابعث الرسالة مع الزر
    sent = context.bot.send_message(
        chat_id=chat_id,
        text="سلام! عندك زر تحت — إضغط باش تشوف الرابط. إذا ما ضغطتيش خلال 5 دقايق غادي نبعت لك رابط آخر.",
        reply_markup=reply_markup
    )

    # إذا كان هناك Job سابق للمستخدم، نلغيوه
    if user_id in user_jobs:
        try:
            user_jobs[user_id].schedule_removal()
        except Exception:
            pass

    # نبرمجو Job لي يتنفذ بعد TIMEOUT_SECONDS
    job = context.job_queue.run_once(
        callback=timeout_callback,
        when=TIMEOUT_SECONDS,
        context={"chat_id": chat_id, "user_id": user_id}
    )
    user_jobs[user_id] = job
    logger.info("Started timeout job for user %s", user_id)


def timeout_callback(context: CallbackContext):
    job_ctx = context.job.context
    chat_id = job_ctx["chat_id"]
    user_id = job_ctx["user_id"]

    # قبل الإرسال نتأكدو أن المستخدم ما ضغطش (إلا تضغطنا غنلّيو ال job)
    # هنا هاد ال job كتبدا إلا متمسحاتش، يعني ما تضغطش
    try:
        context.bot.send_message(
            chat_id=chat_id,
            text=f"مرات كتكون مشغول 😅 — راه مابغاش يضغط، هاهو رابط الاحتياطي: {LINK_ON_TIMEOUT}"
        )
        logger.info("Sent timeout link to user %s", user_id)
    except Exception as e:
        logger.error("Failed to send timeout message to %s: %s", chat_id, e)

    # نحيدو الريفرنس من dict
    if user_id in user_jobs:
        del user_jobs[user_id]


def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    chat_id = query.message.chat.id

    # مهم: لازم نردّ acknowledgment على ال callback
    query.answer()

    # نبعث للرابط المطلوب
    try:
        context.bot.send_message(chat_id=chat_id, text=f"ها الرابط ديال Google: {LINK_ON_PRESS}")
        logger.info("User %s pressed the button — sent google link", user_id)
    except Exception as e:
        logger.error("Error sending link to %s: %s", chat_id, e)

    # نلغيو أي job كان مبرمج للمستخدم
    if user_id in user_jobs:
        try:
            user_jobs[user_id].schedule_removal()
        except Exception:
            pass
        del user_jobs[user_id]


def help_command(update: Update, context: CallbackContext):
    update.message.reply_text("استعمل /start باش تبدا.")


def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CallbackQueryHandler(button_handler, pattern="^press_show_link$"))

    # بداية البوت
    updater.start_polling()
    logger.info("Bot started. Listening...")
    updater.idle()


if __name__ == "__main__":
    main()
