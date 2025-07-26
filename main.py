import logging
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# Configuración
BOT_TOKEN = "8436589239:AAEujmfBEjZD1jpU-LENDewQ5klxWZtPQh0"
ADMIN_USERNAME = "@lester_og"
ADMIN_CHAT_ID = 7926331993  # Tu chat_id

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
        [InlineKeyboardButton("🔥 ABC S5 - 200ips - 20$", callback_data="ABC_200ips_20")],
        [InlineKeyboardButton("🔥 ABC S5 - 400ips - 35$", callback_data="ABC_400ips_35")],
        [InlineKeyboardButton("🔥 ABC S5 - 800ips - 55$", callback_data="ABC_800ips_55")],
        [InlineKeyboardButton("🔥 ABC S5 - 1600ips - 110$", callback_data="ABC_1600ips_110")],
        [InlineKeyboardButton("🔥 ABC S5 - 3400ips - 180$", callback_data="ABC_3400ips_180")],
        [InlineKeyboardButton("🔥 ABC S5 - 1GB - 5.50$", callback_data="ABC_1GB_5.50")],
        [InlineKeyboardButton("🔥 ABC S5 - 5GB - 12$", callback_data="ABC_5GB_12")],
        [InlineKeyboardButton("🔥 ABC S5 - 10GB - 18$", callback_data="ABC_10GB_18")],
        [InlineKeyboardButton("🔥 ABC S5 - 20GB - 30$", callback_data="ABC_20GB_30")],
        [InlineKeyboardButton("🔥 ABC S5 - 50GB - 65$", callback_data="ABC_50GB_65")],
        [InlineKeyboardButton("🔥 PIA S5 - 200ips - 20$", callback_data="PIA_200ips_20")],
        [InlineKeyboardButton("🔥 PIA S5 - 400ips - 35$", callback_data="PIA_400ips_35")],
        [InlineKeyboardButton("🔥 PIA S5 - 800ips - 55$", callback_data="PIA_800ips_55")],
        [InlineKeyboardButton("🔥 PIA S5 - 1600ips - 110$", callback_data="PIA_1600ips_110")],
        [InlineKeyboardButton("🔥 9 PROXY - 200ips - 20$", callback_data="9PROXY_200ips_20")],
        [InlineKeyboardButton("🔥 9 PROXY - 400ips - 35$", callback_data="9PROXY_400ips_35")],
        [InlineKeyboardButton("🔥 9 PROXY - 800ips - 55$", callback_data="9PROXY_800ips_55")],
        [InlineKeyboardButton("🔥 9 PROXY - 2000ips - 120$", callback_data="9PROXY_2000ips_120")],
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# Selección de plan
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    plan = query.data
    user = query.from_user

    cursor.execute("REPLACE INTO orders (user_id, username, plan, wallet_type) VALUES (?, ?, ?, ?)",
                   (user.id, user.username or "SinUsername", plan, ""))
    conn.commit()

    text = f"✅ Plan seleccionado: *{plan.replace('_', ' ')}*\n\nSelecciona la red para el pago:"
    keyboard = [
        [InlineKeyboardButton("💸 USDT TRC20", callback_data="wallet_TRC20")],
        [InlineKeyboardButton("💸 USDT BEP20", callback_data="wallet_BEP20")],
    ]
    await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# Elección de wallet
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
        f"Envía el pago y luego *SOLO la foto del comprobante* aquí para procesar tu orden."
    )
    await query.message.reply_text(text, parse_mode="Markdown")

# Foto del comprobante
async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_id = user.id
    cursor.execute("SELECT plan, wallet_type FROM orders WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()

    if row is None or not row[1]:
        await update.message.reply_text("🚫 No has seleccionado un plan y red de pago. Usa /start para comenzar.")
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
        f"Presiona para enviar la key a este cliente de forma segura."
    )
    await context.bot.send_photo(
        chat_id=ADMIN_CHAT_ID,
        photo=photo,
        caption=caption,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    await update.message.reply_text("✅ Comprobante recibido. Tu pago está en revisión, espera a que el administrador confirme tu key.")

# Botón enviar key seguro
async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("send_key_"):
        user_id = int(data.split("_")[-1])

        # Guardar en bot_data el user_id esperando key asociado al ADMIN_CHAT_ID
        if "awaiting_keys" not in context.bot_data:
            context.bot_data["awaiting_keys"] = {}

        context.bot_data["awaiting_keys"][ADMIN_CHAT_ID] = user_id

        await query.message.reply_text(f"✏️ Envía la *key* que deseas entregar a este cliente ahora.", parse_mode="Markdown")

# Recepción de key segura
async def key_delivery_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "awaiting_keys" in context.bot_data and ADMIN_CHAT_ID in context.bot_data["awaiting_keys"]:
        user_id = context.bot_data["awaiting_keys"][ADMIN_CHAT_ID]
        key_text = update.message.text

        await context.bot.send_message(
            chat_id=user_id,
            text=f"🎉 *Pago confirmado.* Aquí está tu key:\n\n`{key_text}`\n\nGracias por tu compra.",
            parse_mode="Markdown"
        )
        await update.message.reply_text("✅ Key enviada correctamente al cliente.")

        cursor.execute("DELETE FROM orders WHERE user_id = ?", (user_id,))
        conn.commit()

        del context.bot_data["awaiting_keys"][ADMIN_CHAT_ID]
    else:
        await update.message.reply_text("🚫 No estás confirmando ninguna key actualmente.")

# Mensaje de texto no válido
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚫 Solo se acepta la *foto del comprobante de pago* o la *key* si eres administrador.",
        parse_mode="Markdown"
    )

# Main
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^(ABC_|PIA_|9PROXY_)"))
    app.add_handler(CallbackQueryHandler(wallet_selection_handler, pattern="^wallet_"))
    app.add_handler(CallbackQueryHandler(callback_query_handler, pattern="^send_key_"))
    app.add_handler(MessageHandler(filters.PHOTO & filters.ChatType.PRIVATE, photo_handler))
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, key_delivery_handler))
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, text_handler))
    app.run_polling()

if __name__ == "__main__":
    main()
