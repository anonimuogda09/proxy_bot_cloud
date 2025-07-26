import logging
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# Configuración
BOT_TOKEN = "8436589239:AAEujmfBEjZD1jpU-LENDewQ5klxWZtPQh0"
ADMIN_USERNAME = "@lester_og"
ADMIN_CHAT_ID = 7926331993

# DB init
conn = sqlite3.connect("orders.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS orders (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    plan TEXT,
    wallet_type TEXT
)
''')
conn.commit()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"/start ejecutado por {update.effective_user.id}")
    keyboard = [
        [InlineKeyboardButton("🔥 PIA S5 - 200 IPs - 20$", callback_data="PIA_200")],
        [InlineKeyboardButton("🔥 ABC S5 - 1GB - 5.50$", callback_data="ABC_1GB")]
    ]
    await update.message.reply_text(
        "🤖 *Bienvenido al Bot de Proxies!* Elige un plan para comenzar:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# Comando /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"/help ejecutado por {update.effective_user.id}")
    await update.message.reply_text(
        f"ℹ️ *Ayuda:*\n\n"
        "Para comprar proxies:\n"
        "✅ Envía /start y elige el plan.\n"
        "✅ Selecciona la red de pago (TRC20 o BEP20).\n"
        "✅ Envía la foto del comprobante aquí.\n\n"
        f"👨‍💻 Si necesitas soporte, escribe a {ADMIN_USERNAME}.",
        parse_mode="Markdown"
    )

# Button Handler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    plan = query.data
    user = query.from_user
    cursor.execute("REPLACE INTO orders (user_id, username, plan, wallet_type) VALUES (?, ?, ?, ?)",
                   (user.id, user.username or "SinUsername", plan, ""))
    conn.commit()
    await query.message.reply_text(
        f"✅ Plan seleccionado: *{plan.replace('_',' ')}*\n\nSelecciona la red para el pago:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("USDT TRC20", callback_data="wallet_TRC20")],
            [InlineKeyboardButton("USDT BEP20", callback_data="wallet_BEP20")]
        ]),
        parse_mode="Markdown"
    )

# Wallet Handler
async def wallet_selection_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    data = query.data
    if data == "wallet_TRC20":
        wallet = "TP1PTzXWzyySpEiM6paWRL9rFZwF3M9wzn"
        wallet_type = "USDT TRC20"
    elif data == "wallet_BEP20":
        wallet = "0x5f3a2fab94fbefdf0eca1c695edcbe05c6130f5b"
        wallet_type = "USDT BEP20"
    else:
        return
    cursor.execute("UPDATE orders SET wallet_type = ? WHERE user_id = ?", (wallet_type, user.id))
    conn.commit()
    await query.message.reply_text(
        f"💰 *Dirección de pago para {wallet_type}:*\n\n`{wallet}`\n\n"
        "Envía la foto del comprobante aquí cuando hayas realizado el pago.",
        parse_mode="Markdown"
    )

# Foto comprobante
async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    cursor.execute("SELECT plan, wallet_type FROM orders WHERE user_id = ?", (user.id,))
    row = cursor.fetchone()
    if not row or not row[1]:
        await update.message.reply_text("🚫 Debes seleccionar un plan y red de pago primero. Usa /start.")
        return
    plan, wallet_type = row
    caption = (
        f"🧾 *Nuevo pago recibido*\n\n"
        f"👤 @{user.username or 'SinUsername'}\n"
        f"🆔 `{user.id}`\n"
        f"📦 Plan: *{plan.replace('_',' ')}*\n"
        f"💰 Wallet: *{wallet_type}*"
    )
    keyboard = [[InlineKeyboardButton("✅ Enviar Key", callback_data=f"send_key_{user.id}")]]
    await context.bot.send_photo(chat_id=ADMIN_CHAT_ID, photo=update.message.photo[-1].file_id,
                                 caption=caption, reply_markup=InlineKeyboardMarkup(keyboard),
                                 parse_mode="Markdown")
    await update.message.reply_text("✅ Comprobante recibido. Espera confirmación del admin.")

# Confirmar envío de key
async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith("send_key_"):
        user_id = int(data.split("_")[-1])
        context.user_data["awaiting_key_for"] = user_id
        await query.message.reply_text("✏️ Envía ahora la *key* a entregar al cliente.")

# Enviar key
async def key_delivery_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "awaiting_key_for" in context.user_data:
        user_id = context.user_data.pop("awaiting_key_for")
        await context.bot.send_message(
            chat_id=user_id,
            text=f"🎉 *Pago confirmado.* Aquí está tu key:\n\n`{update.message.text}`\n\nGracias por tu compra.",
            parse_mode="Markdown"
        )
        await update.message.reply_text("✅ Key enviada correctamente.")
        cursor.execute("DELETE FROM orders WHERE user_id = ?", (user_id,))
        conn.commit()
    else:
        await update.message.reply_text("🚫 No estás confirmando ninguna key en este momento.")

# Texto no válido
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚫 Solo se acepta la *foto del comprobante de pago* o la *key* si eres administrador.",
        parse_mode="Markdown"
    )

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^(PIA_|ABC_)"))
    app.add_handler(CallbackQueryHandler(wallet_selection_handler, pattern="^wallet_"))
    app.add_handler(CallbackQueryHandler(callback_query_handler, pattern="^send_key_"))
    app.add_handler(MessageHandler(filters.PHOTO & filters.ChatType.PRIVATE, photo_handler))
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, key_delivery_handler))
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, text_handler))
    app.run_polling()

if __name__ == "__main__":
    main()
