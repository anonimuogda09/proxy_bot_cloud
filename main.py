import logging
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# Configuración
BOT_TOKEN = "8436589239:AAEujmfBEjZD1jpU-LENDewQ5klxWZtPQh0"
ADMIN_USERNAME = "@lester_og"
ADMIN_CHAT_ID = 7926331993

# Inicializar DB
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
    text = "🤖 *Bienvenido al Bot de Proxies!*\n\nSelecciona un plan para continuar:"
    keyboard = [
        [InlineKeyboardButton("🔥 PIA S5 - 200 IPs - 20$", callback_data="PIA_200")],
        [InlineKeyboardButton("🔥 PIA S5 - 400 IPs - 35$", callback_data="PIA_400")],
        [InlineKeyboardButton("🔥 PIA S5 - 800 IPs - 55$", callback_data="PIA_800")],
        [InlineKeyboardButton("🔥 PIA S5 - 1600 IPs - 110$", callback_data="PIA_1600")],
        [InlineKeyboardButton("🔥 ABC S5 - 1GB - 5.50$", callback_data="ABC_1GB")],
        [InlineKeyboardButton("🔥 ABC S5 - 5GB - 12$", callback_data="ABC_5GB")],
        [InlineKeyboardButton("🔥 ABC S5 - 10GB - 18$", callback_data="ABC_10GB")],
        [InlineKeyboardButton("🔥 ABC S5 - 20GB - 30$", callback_data="ABC_20GB")],
        [InlineKeyboardButton("🔥 ABC S5 - 50GB - 65$", callback_data="ABC_50GB")],
        [InlineKeyboardButton("🔥 9PROXY - 200 IPs - 20$", callback_data="9PROXY_200")],
        [InlineKeyboardButton("🔥 9PROXY - 400 IPs - 35$", callback_data="9PROXY_400")],
        [InlineKeyboardButton("🔥 9PROXY - 800 IPs - 55$", callback_data="9PROXY_800")],
        [InlineKeyboardButton("🔥 9PROXY - 2000 IPs - 120$", callback_data="9PROXY_2000")],
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# Comando /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📚 *Ayuda del Bot de Proxies*\n\n"
        "✅ Usa /start para ver los planes disponibles y comenzar tu compra.\n"
        "✅ Selecciona la red de pago y envía tu comprobante.\n"
        "✅ Recibirás tu key tras la confirmación.\n\n"
        f"🚨 *Soporte*: Si tienes dudas o problemas, escríbeme directo aquí:\n{ADMIN_USERNAME}\n\n"
        "🤖 Gracias por usar el bot de proxies."
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

# Selección de plan
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    plan = query.data
    user = query.from_user

    cursor.execute("REPLACE INTO orders (user_id, username, plan, wallet_type) VALUES (?, ?, ?, ?)",
                   (user.id, user.username or "SinUsername", plan, ""))
    conn.commit()

    text = f"✅ Plan seleccionado: *{plan.replace('_', ' ')}*\n\nSelecciona la red de pago:"
    keyboard = [
        [InlineKeyboardButton("USDT TRC20", callback_data="wallet_TRC20")],
        [InlineKeyboardButton("USDT BEP20", callback_data="wallet_BEP20")],
    ]
    await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# Selección de wallet
async def wallet_selection_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user = query.from_user

    if data == "wallet_TRC20":
        wallet_address = "TP1PTzXWzyySpEiM6paWRL9rFZwF3M9wzn"
        wallet_type = "USDT TRC20"
    elif data == "wallet_BEP20":
        wallet_address = "0x5f3a2fab94fbefdf0eca1c695edcbe05c6130f5b"
        wallet_type = "USDT BEP20"
    else:
        return

    cursor.execute("UPDATE orders SET wallet_type = ? WHERE user_id = ?", (wallet_type, user.id))
    conn.commit()

    text = (
        f"💰 *Dirección de pago para {wallet_type}:*\n\n"
        f"`{wallet_address}`\n\n"
        "Envía el pago y luego *SOLO la foto del comprobante* aquí."
    )
    await query.message.reply_text(text, parse_mode="Markdown")

# Foto del comprobante
async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_id = user.id
    cursor.execute("SELECT plan, wallet_type FROM orders WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()

    if row is None or not row[1]:
        await update.message.reply_text("🚫 Usa /start y selecciona plan y red antes de enviar el comprobante.")
        return

    plan = row[0].replace('_', ' ')
    wallet_type = row[1]
    photo = update.message.photo[-1].file_id

    keyboard = [[InlineKeyboardButton("✅ Enviar Key", callback_data=f"send_key_{user_id}")]]
    caption = (
        f"🧾 *Nuevo Pago Recibido*\n\n"
        f"👤 Usuario: @{user.username or 'SinUsername'}\n"
        f"🆔 ID: `{user_id}`\n"
        f"📦 Plan: *{plan}*\n"
        f"💰 Wallet: *{wallet_type}*\n\n"
        "Presiona para enviar la key al cliente."
    )
    await context.bot.send_photo(
        chat_id=ADMIN_CHAT_ID,
        photo=photo,
        caption=caption,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    await update.message.reply_text("✅ Comprobante recibido. Tu pago está en revisión, espera confirmación.")

# Confirmación y envío de key
async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("send_key_"):
        user_id = int(data.split("_")[-1])
        context.user_data["awaiting_key_for"] = user_id
        await query.message.reply_text("✏️ Envía *ahora la key* que deseas entregar a este cliente.")

# Recepción de key y entrega al cliente
async def key_delivery_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "awaiting_key_for" in context.user_data:
        user_id = context.user_data["awaiting_key_for"]
        key_text = update.message.text

        await context.bot.send_message(
            chat_id=user_id,
            text=f"🎉 *Pago confirmado.* Aquí está tu key:\n\n`{key_text}`\n\nGracias por tu compra.",
            parse_mode="Markdown"
        )
        await update.message.reply_text("✅ Key enviada correctamente al cliente.")
        cursor.execute("DELETE FROM orders WHERE user_id = ?", (user_id,))
        conn.commit()
        del context.user_data["awaiting_key_for"]
    else:
        await update.message.reply_text("🚫 No estás confirmando ninguna key actualmente.")

# Mensaje de texto no válido
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚫 Solo se acepta la *foto del comprobante de pago* o la *key* si eres administrador.",
        parse_mode="Markdown"
    )

# Main para Railway
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^(PIA_|ABC_|9PROXY_)"))
    app.add_handler(CallbackQueryHandler(wallet_selection_handler, pattern="^wallet_"))
    app.add_handler(CallbackQueryHandler(callback_query_handler, pattern="^send_key_"))
    app.add_handler(MessageHandler(filters.PHOTO & filters.ChatType.PRIVATE, photo_handler))
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, key_delivery_handler))
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, text_handler))
    app.run_polling()

if __name__ == "__main__":
    main()
