import os
import logging
import psycopg2
from telegram import Update, ForceReply
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters

# Временные пароли и ID
ADMIN_PASSWORD = "1234"
AUTHORIZED_ADMINS = {}  # user_id -> warehouse ("china" or "tajikistan")

# Подключение к PostgreSQL
conn = psycopg2.connect(
    host=os.getenv("DB_HOST", "db.example.com"),
    database=os.getenv("DB_NAME", "trackdb"),
    user=os.getenv("DB_USER", "admin"),
    password=os.getenv("DB_PASSWORD", "admin123"),
    port=os.getenv("DB_PORT", "5432")
)
cursor = conn.cursor()

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Добро пожаловать! Отправьте /status <номер>, чтобы узнать статус вашего товара.")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Пожалуйста, введите номер: /status <номер>")
        return

    number = args[0]
    cursor.execute("SELECT status FROM packages WHERE number = %s", (number,))
    result = cursor.fetchone()
    if result:
        await update.message.reply_text(f"Статус: {result[0]}")
    else:
        await update.message.reply_text("Информация о товаре не найдена.")

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите пароль для входа:")

    return 1  # Переход к состоянию ожидания пароля

async def check_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    password = update.message.text
    if password == ADMIN_PASSWORD:
        user_id = update.message.from_user.id
        context.user_data["admin_id"] = user_id
        await update.message.reply_text("Выберите склад: /china или /tajikistan")
        return 2
    else:
        await update.message.reply_text("Неверный пароль.")
        return ConversationHandler.END

async def set_warehouse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    warehouse = update.message.text.lstrip("/")
    admin_id = context.user_data.get("admin_id")
    if warehouse in ["china", "tajikistan"]:
        AUTHORIZED_ADMINS[admin_id] = warehouse
        await update.message.reply_text(f"Вы вошли как админ склада {warehouse}.")
    else:
        await update.message.reply_text("Неверный склад.")
    return ConversationHandler.END

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if AUTHORIZED_ADMINS.get(user_id) != "china":
        return

    args = context.args
    if not args:
        await update.message.reply_text("Введите номер: /add <номер>")
        return
    number = args[0]

    cursor.execute("INSERT INTO packages (number, status) VALUES (%s, %s) ON CONFLICT (number) DO NOTHING", (number, "Принят на складе в Китае"))
    conn.commit()

    await update.message.reply_text(f"Добавлен номер: {number}")

async def arrived(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if AUTHORIZED_ADMINS.get(user_id) != "tajikistan":
        return

    args = context.args
    if not args:
        await update.message.reply_text("Введите номер: /arrived <номер>")
        return
    number = args[0]

    cursor.execute("UPDATE packages SET status = %s WHERE number = %s", ("Прибыл в Таджикистан", number))
    conn.commit()

    await update.message.reply_text(f"Обновлён номер: {number}")

def main():
    token = os.getenv("BOT_TOKEN", "YOUR_TOKEN_HERE")
    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("arrived", arrived))

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("admin", admin)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, check_password)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_warehouse)],
        },
        fallbacks=[],
    )
    app.add_handler(conv_handler)

    app.run_polling()

if __name__ == "__main__":
    main()