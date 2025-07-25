# Generando y preparando el archivo main.py limpio, comentado y funcional con SQLite
# para automatización de venta de proxies con confirmación manual por parte del admin.

main_code = """
import logging
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# Configuración
BOT_TOKEN = "8436589239:AAEujmfBEjZD1jpU-LENDewQ5klxWZtPQh0"
ADMIN_USERNAME = "@lester_og"  # Para mostrar en mensajes
ADMIN_CHAT_ID = 123456789      # 🚩 Coloca aquí tu chat_id de Telegram (te lo puedo generar si no lo sabes)

# Inicializar DB
conn = sqlite3.connect("orders.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS orders (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    plan TEXT
)
''')
conn.commit()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Comandos
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "🤖 *Bienvenido al Bot de Proxies!*\n\nSelecciona un plan para continuar:"
    keyboard = [
        [InlineKeyboardButton("🔥 PIA S5 - 200 IPs - 20$", callback_data="PIA_200")],
        [InlineKeyboardButton("🔥 ABC S5 - 1GB - 5.50$", callback_data="ABC_1GB")],
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    plan = query.data
    user = query.from_user
    cursor.execute("REPLACE INTO orders (user_id, username, plan) VALUES (?, ?, ?)",
                   (user.id, user.username or "SinUsername", plan))
    conn.commit()
    await query.message.reply_text(
        "✅ Plan seleccionado: *{}*\n\nPor favor, envía *SOLO la foto del comprobante de pago* para procesar tu orden.".format(plan.replace("_", " ")),
        parse_mode="Markdown"
    )

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_id = user.id
    cursor.execute("SELECT plan FROM orders WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()

    if row is None:
        await update.message.reply_text("🚫 No has seleccionado un plan. Usa /start para elegir un plan antes de enviar tu comprobante.")
        return

    plan = row[0].replace("_", " ")
    # Enviar al admin
    photo = update.message.photo[-1].file_id
    keyboard = [[InlineKeyboardButton("✅ Enviar Key", callback_data=f"send_key_{user_id}")]]
    caption = f"🧾 *Nuevo Pago Recibido*\n\n👤 Usuario: @{user.username or 'SinUsername'}\n🆔 ID: `{user_id}`\n📦 Plan: *{plan}*\n\nPor favor, presiona el botón para enviar la key."
    await context.bot.send_photo(
        chat_id=ADMIN_CHAT_ID,
        photo=photo,
        caption=caption,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    await update.message.reply_text("✅ Comprobante recibido. Tu pago está en revisión, espera a que el administrador confirme tu key.")

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚫 Solo se acepta la *foto del comprobante de pago*. Por favor, envía únicamente la imagen del pago.", parse_mode="Markdown")

async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("send_key_"):
        user_id = int(data.split("_")[-1])
        context.user_data["awaiting_key_for"] = user_id
        await query.message.reply_text("✏️ Envía la *key* que deseas entregar al cliente.")
        return

async def key_delivery_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "awaiting_key_for" in context.user_data:
        user_id = context.user_data["awaiting_key_for"]
        key_text = update.message.text

        # Enviar al cliente
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

# Main
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^(PIA_|ABC_)"))
    app.add_handler(CallbackQueryHandler(callback_query_handler, pattern="^send_key_"))
    app.add_handler(MessageHandler(filters.PHOTO & filters.ChatType.PRIVATE, photo_handler))
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, key_delivery_handler))
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, text_handler))
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
"""

# Guardar el archivo listo para el usuario
with open("/mnt/data/main.py", "w", encoding="utf-8") as f:
    f.write(main_code)

# Listo para entregar
"/mnt/data/main.py listo para descargar y reemplazar en Railway"

