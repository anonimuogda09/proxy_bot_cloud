from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, CallbackQueryHandler, filters

OWNER_USERNAME = "@lester_og"
OWNER_CHAT_ID = 7926331993 # Cambiar por tu chat_id numérico
USDT_WALLET = "TP1PTzXWzyySpEiM6paWRL9rFZwF3M9wzn"

purchase_options = [
    ("ABC S5 200 IPs - $20", "abc_200"),
    ("ABC S5 400 IPs - $35", "abc_400"),
    ("ABC S5 800 IPs - $55", "abc_800"),
    ("ABC S5 1600 IPs - $110", "abc_1600"),
    ("PÍA S5 200 IPs - $20", "pia_200"),
    ("PÍA S5 400 IPs - $35", "pia_400"),
    ("PÍA S5 800 IPs - $55", "pia_800"),
    ("PÍA S5 1600 IPs - $110", "pia_1600"),
    ("9 PROXY 200 IPs - $20", "9proxy_200"),
    ("9 PROXY 400 IPs - $35", "9proxy_400"),
    ("9 PROXY 800 IPs - $55", "9proxy_800"),
    ("9 PROXY 2000 IPs - $120", "9proxy_2000")
]

def load_keys(file):
    try:
        with open(file, "r") as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    except FileNotFoundError:
        return []

def pop_key(file):
    keys = load_keys(file)
    if keys:
        key = keys.pop(0)
        with open(file, "w") as f:
            for k in keys:
                f.write(k + "\n")
        return key
    else:
        return "❌ Sin stock para este plan. Contacta soporte."

pia_keys_file = "pia_keys.txt"
abc_keys_file = "abc_keys.txt"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 *Bienvenido a Proxy Bot S5/ABC*\n\n"
        "Usa /comprar para ver precios y formas de pago.\n"
        "Usa /stock para ver proxies disponibles.\n"
        "Usa /help si necesitas asistencia."
    )

async def comprar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(text=name, callback_data=code)] for name, code in purchase_options]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🛒 *Selecciona la opción que deseas comprar:*",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    item = query.data
    context.user_data['pedido'] = item

    await query.edit_message_text(
        f"✅ Seleccionaste: *{item.replace('_', ' ').upper()}*\n\n"
        f"💸 Envía el pago correspondiente a la siguiente wallet USDT (TRC20):\n`{USDT_WALLET}`\n\n"
        f"Tras el pago, envía aquí el comprobante de transacción para validarlo y recibir tus proxies."
    )

async def stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"📦 *Stock Disponible:*\n"
        f"- PÍA Proxy S5: {len(load_keys(pia_keys_file))} disponibles\n"
        f"- ABC S5-ABC GB: {len(load_keys(abc_keys_file))} disponibles\n\n"
        "Compra ahora antes de que se agoten."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👨‍💻 *Soporte:*\n"
        f"Si tienes dudas, escribe aquí o contacta {OWNER_USERNAME}.\n"
        "Tras el pago, envía el comprobante aquí para recibir tus proxies."
    )

async def forward_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    chat_id = update.message.chat_id
    context.user_data['buyer_chat_id'] = chat_id

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Confirmar", callback_data=f"confirm_{chat_id}")]
    ])

    if update.message.photo:
        file_id = update.message.photo[-1].file_id
        await context.bot.send_photo(
            chat_id=OWNER_CHAT_ID,
            photo=file_id,
            caption=f"💰 *Nuevo comprobante de pago de @{user.username or user.id}*\nID: {user.id}",
            reply_markup=keyboard
        )
    else:
        await context.bot.send_message(
            chat_id=OWNER_CHAT_ID,
            text=f"💰 *Nuevo comprobante de pago de @{user.username or user.id}*\nID: {user.id}\n\n{update.message.text}",
            reply_markup=keyboard
        )

    await update.message.reply_text("✅ Comprobante enviado para revisión. Recibirás tu proxy tras la verificación.")

async def confirm_delivery(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, buyer_chat_id = query.data.split("_")
    buyer_chat_id = int(buyer_chat_id)

    pedido = context.user_data.get('pedido', 'sin_selección')
    if pedido.startswith("pia"):
        key = pop_key(pia_keys_file)
    elif pedido.startswith("abc"):
        key = pop_key(abc_keys_file)
    else:
        key = "❌ No se pudo identificar el plan. Contacta al admin."

    await context.bot.send_message(
        chat_id=buyer_chat_id,
        text=f"🎉 *Pago confirmado.* Aquí está tu proxy:\n\n`{key}`\n\nGracias por tu compra."
    )
    await query.edit_message_text("✅ Proxy enviado al cliente.")

app = ApplicationBuilder().token("8436589239:AAEujmfBEjZD1jpU-LENDewQ5klxWZtPQh0").build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("comprar", comprar))
app.add_handler(CommandHandler("stock", stock))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CallbackQueryHandler(button_handler, pattern="^(?!confirm_).*"))
app.add_handler(CallbackQueryHandler(confirm_delivery, pattern="^confirm_"))
app.add_handler(MessageHandler(filters.PHOTO | filters.TEXT & (~filters.COMMAND), forward_confirmation))

print("🤖 Bot corriendo y listo con autoentrega tras confirmación...")

app.run_polling()
