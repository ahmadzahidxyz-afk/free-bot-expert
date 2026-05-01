from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from screener import (
    get_stock_info, format_output, format_output_4h, format_output_scalping, format_output_akumulasi,
    ISSI_BATCHES, cari_rekomendasi_stoch, cari_akumulasi, cari_rekomendasi_swing_cepat,
    cari_rekomendasi_scalping
)
import asyncio
import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8527186820:AAE6fobpKT8TkFDTW9M3PgLhnBH8ohQKeZg"
BOT_CREATOR = {"name": "Anggi Munawar", "username": "@ALPHAfinanceid", "instagram": "https://www.instagram.com/anggimnwr", "version": "3.1.0"}

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(f"❌ Error: {str(context.error)[:100]}")
    except:
        pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (f"🤖 Screener v{BOT_CREATOR['version']}\nby {BOT_CREATOR['name']}\n\n"
           "• /rekomendasi — mencari Rekomendasi Swing Daily\n"
           "• /swing_cepat — ⚡ mencari swing 4H:\n"
           "• /scalping — 🎯 Daily: Mencari saham scalping\n"
           "• /akumulasi — 📈 mencari saham yang sedang di akumulasi\n"
           "• /scan — Analisa individu\n"
           "• /about — Info bot\n\n📌 Contoh: /scan BBRI.JK")
    keyboard = [
        [InlineKeyboardButton("👨‍💻 About", callback_data="about"), 
         InlineKeyboardButton("📈 Akumulasi", callback_data="akumulasi")],
        [InlineKeyboardButton("⚡ Swing Cepat", callback_data="swing_cepat"), 
         InlineKeyboardButton("🎯 Scalping", callback_data="scalping")],
        [InlineKeyboardButton("📈 Swing", callback_data="rekomendasi"), 
         InlineKeyboardButton("📋 Semua", callback_data="all")]
    ]
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        msg = (f"🤖 SCREENER v{BOT_CREATOR['version']}\n👨‍💻 {BOT_CREATOR['name']}\n📱 IG: {BOT_CREATOR['instagram']}\n\n"
               "📊 Fitur:\n"
               "• /rekomendasi - Daily\n"
               "• /swing_cepat - 4H:\n"
               "• /scalping - Daily:\n"
               "  📈 Menampilkan 1 Day Return (%)\n"
               "• /akumulasi -\n"
               "  **TP: +21% dari HIGH**\n"
               "• /scan SYMBOL - Analisa individu\n\n"
               "🔧 Tech: Python, yfinance")
        keyboard = [
            [InlineKeyboardButton("📱 Instagram", url=BOT_CREATOR['instagram'])], 
            [InlineKeyboardButton("🔙 Menu", callback_data="start")]
        ]
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text=msg, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        logger.error(f"About error: {e}")
        if update.callback_query:
            await update.callback_query.message.reply_text(f"❌ Error: {str(e)[:100]}")
        else:
            await update.message.reply_text(f"❌ Error: {str(e)[:100]}")

async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: 
        return await update.message.reply_text("❌ Gunakan: /scan SYMBOL\nContoh: /scan BBRI.JK")
    sym = context.args[0].upper()
    await update.message.reply_text(f"⏳ Scanning {sym}...")
    data = get_stock_info(sym)
    await update.message.reply_text(format_output(data) if data else f"❌ Data {sym} tidak ditemukan")

def get_symbols():
    symbols, seen = [], set()
    for batch in ISSI_BATCHES:
        for sym in batch if isinstance(batch, list) else [batch]:
            if sym not in seen: 
                seen.add(sym)
                symbols.append(sym)
    return symbols

async def rekomendasi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.callback_query:
            await update.callback_query.edit_message_text("⏳ Mencari swing (Daily)...")
            msg_func = update.callback_query.message.reply_text
        else:
            await update.message.reply_text("⏳ Mencari swing (Daily)...")
            msg_func = update.message.reply_text
        
        symbols = get_symbols()
        await msg_func(f"📈 Scanning {len(symbols)} saham...")
        results = cari_rekomendasi_stoch(symbols)
        
        if not results: 
            return await msg_func("❌ Tidak ada saham yang memenuhi kriteria.")
        
        await msg_func(f"✅ Ditemukan {len(results)} saham")
        for i, data in enumerate(results, 1):
            await msg_func(f"📊 #{i}: {data['symbol']} (K={data['stoch_k']:.1f})\n" + format_output(data))
            await asyncio.sleep(0.5)
        
        summary = f"✅ SELESAI!\n📊 Dipindai: {len(symbols)}\n✅ Ditemukan: {len(results)}\n👨‍💻 {BOT_CREATOR['name']}"
        keyboard = [
            [InlineKeyboardButton("👨‍💻 About", callback_data="about"), 
             InlineKeyboardButton("📈 Akumulasi", callback_data="akumulasi")],
            [InlineKeyboardButton("⚡ Swing Cepat", callback_data="swing_cepat"), 
             InlineKeyboardButton("🎯 Scalping", callback_data="scalping")],
            [InlineKeyboardButton("🔙 Menu", callback_data="start")]
        ]
        await msg_func(summary, reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        logger.error(f"Rekomendasi error: {e}")
        if update.callback_query:
            await update.callback_query.message.reply_text(f"❌ Error: {str(e)[:100]}")
        else:
            await update.message.reply_text(f"❌ Error: {str(e)[:100]}")

async def akumulasi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.callback_query:
            await update.callback_query.edit_message_text("📈 Mencari akumulasi")
            msg_func = update.callback_query.message.reply_text
        else:
            await update.message.reply_text("📈 Mencari akumulasi")
            msg_func = update.message.reply_text
        
        symbols = get_symbols()
        await msg_func(f"📈 Scanning {len(symbols)} saham (Fibonacci 3mo)...")
        results = cari_akumulasi(symbols)
        
        if not results: 
            return await msg_func("❌ Tidak ada saham di area akumulasi.")
        
        await msg_func(f"✅ Ditemukan {len(results)} saham")
        for i, data in enumerate(results, 1):
            await msg_func(f"📈 #{i}: {data['symbol']}\n" + format_output_akumulasi(data))
            await asyncio.sleep(0.5)
        
        summary = f"✅ SELESAI!\n📊 Dipindai: {len(symbols)}\n✅ Ditemukan: {len(results)}\n👨‍💻 {BOT_CREATOR['name']}"
        keyboard = [
            [InlineKeyboardButton("👨‍💻 About", callback_data="about"), 
             InlineKeyboardButton("⚡ Swing Cepat", callback_data="swing_cepat")],
            [InlineKeyboardButton("🎯 Scalping", callback_data="scalping"), 
             InlineKeyboardButton("📈 Swing", callback_data="rekomendasi")],
            [InlineKeyboardButton("🔙 Menu", callback_data="start")]
        ]
        await msg_func(summary, reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        logger.error(f"Akumulasi error: {e}")
        if update.callback_query:
            await update.callback_query.message.reply_text(f"❌ Error: {str(e)[:100]}")
        else:
            await update.message.reply_text(f"❌ Error: {str(e)[:100]}")

async def swing_cepat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.callback_query:
            await update.callback_query.edit_message_text("⏳ Mencari swing cepat (4H)...")
            msg_func = update.callback_query.message.reply_text
        else:
            await update.message.reply_text("⏳ Mencari swing cepat (4H)...")
            msg_func = update.message.reply_text
        
        symbols = get_symbols()
        await msg_func(f"📈 Scanning {len(symbols)} saham (4H)...")
        results = cari_rekomendasi_swing_cepat(symbols)
        
        if not results: 
            return await msg_func("❌ Tidak ada saham yang memenuhi kriteria.")
        
        await msg_func(f"✅ Ditemukan {len(results)} saham")
        for i, data in enumerate(results, 1):
            await msg_func(f"⚡ #{i}: {data['symbol']} (K={data['stoch_k']:.1f})\n" + format_output_4h(data))
            await asyncio.sleep(0.5)
        
        summary = f"✅ SELESAI!\n📊 Dipindai: {len(symbols)}\n✅ Ditemukan: {len(results)}\n👨‍💻 {BOT_CREATOR['name']}"
        keyboard = [
            [InlineKeyboardButton("👨‍💻 About", callback_data="about"), 
             InlineKeyboardButton("📈 Akumulasi", callback_data="akumulasi")],
            [InlineKeyboardButton("🎯 Scalping", callback_data="scalping"), 
             InlineKeyboardButton("📈 Swing", callback_data="rekomendasi")],
            [InlineKeyboardButton("🔙 Menu", callback_data="start")]
        ]
        await msg_func(summary, reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        logger.error(f"Swing cepat error: {e}")
        if update.callback_query:
            await update.callback_query.message.reply_text(f"❌ Error: {str(e)[:100]}")
        else:
            await update.message.reply_text(f"❌ Error: {str(e)[:100]}")

async def scalping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.callback_query:
            await update.callback_query.edit_message_text("🎯 Mencari scalping (Daily)...")
            msg_func = update.callback_query.message.reply_text
        else:
            await update.message.reply_text("🎯 Mencari scalping (Daily)...")
            msg_func = update.message.reply_text
        
        symbols = get_symbols()
        await msg_func(f"📈 Scanning {len(symbols)} saham (Daily)...")
        results = cari_rekomendasi_scalping(symbols)
        
        if not results: 
            return await msg_func("❌ Tidak ada saham yang memenuhi kriteria.\n\nKriteria:\n• Harga > MA5 + 1\n• Volume > 500rb\n• Value > 500jt\n• RSI > 45")
        
        await msg_func(f"✅ Ditemukan {len(results)} saham")
        for i, data in enumerate(results, 1):
            await msg_func(f"🎯 #{i}: {data['symbol']} (Return: {data['daily_return']:+.2f}%)\n" + format_output_scalping(data))
            await asyncio.sleep(0.5)
        
        summary = f"✅ SELESAI!\n📊 Dipindai: {len(symbols)}\n✅ Ditemukan: {len(results)}\n👨‍💻 {BOT_CREATOR['name']}"
        keyboard = [
            [InlineKeyboardButton("👨‍💻 About", callback_data="about"), 
             InlineKeyboardButton("📈 Akumulasi", callback_data="akumulasi")],
            [InlineKeyboardButton("⚡ Swing Cepat", callback_data="swing_cepat"), 
             InlineKeyboardButton("📈 Swing", callback_data="rekomendasi")],
            [InlineKeyboardButton("🔙 Menu", callback_data="start")]
        ]
        await msg_func(summary, reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        logger.error(f"Scalping error: {e}")
        if update.callback_query:
            await update.callback_query.message.reply_text(f"❌ Error: {str(e)[:100]}")
        else:
            await update.message.reply_text(f"❌ Error: {str(e)[:100]}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    try:
        if data == "about":
            await about(update, context)
        elif data == "akumulasi":
            await akumulasi(update, context)
        elif data == "swing_cepat":
            await swing_cepat(update, context)
        elif data == "scalping":
            await scalping(update, context)
        elif data == "rekomendasi":
            await rekomendasi(update, context)
        elif data == "all":
            msg = ("📊 SEMUA COMMANDS\n\n"
                   "• /rekomendasi - Daily:\n"
                   "• /swing_cepat - 4H:\n"
                   "• /scalping - Daily:\n"
                   "  📈 Menampilkan 1 Day Return (%)\n"
                   "• /akumulasi -\n"
                   "  **TP: +21% dari HIGH**\n"
                   "• /scan SYMBOL - Contoh: /scan BBRI.JK\n"
                   "• /about - Info bot")
            keyboard = [
                [InlineKeyboardButton("📈 Akumulasi", callback_data="akumulasi"), 
                 InlineKeyboardButton("⚡ Swing Cepat", callback_data="swing_cepat")],
                [InlineKeyboardButton("🎯 Scalping", callback_data="scalping"), 
                 InlineKeyboardButton("📈 Swing", callback_data="rekomendasi")],
                [InlineKeyboardButton("🔙 Menu", callback_data="start")]
            ]
            await query.edit_message_text(text=msg, reply_markup=InlineKeyboardMarkup(keyboard))
        elif data == "start":
            msg = (f"🤖 Screener v{BOT_CREATOR['version']}\nby {BOT_CREATOR['name']}\n\n"
                   "• /rekomendasi - Swing Daily\n• /swing_cepat - ⚡ 4H\n• /scalping - 🎯 Daily\n"
                   "• /akumulasi - 📈 Fibonacci\n• /scan - Analisa\n• /about - Info")
            keyboard = [
                [InlineKeyboardButton("📈 Akumulasi", callback_data="akumulasi"), 
                 InlineKeyboardButton("⚡ Swing Cepat", callback_data="swing_cepat")],
                [InlineKeyboardButton("🎯 Scalping", callback_data="scalping"), 
                 InlineKeyboardButton("📈 Swing", callback_data="rekomendasi")],
                [InlineKeyboardButton("👨‍💻 About", callback_data="about"), 
                 InlineKeyboardButton("📋 Semua", callback_data="all")]
            ]
            await query.edit_message_text(text=msg, reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        logger.error(f"Button handler error: {e}")
        await query.edit_message_text(f"❌ Error: {str(e)[:100]}")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("about", about))
    app.add_handler(CommandHandler("scan", scan))
    app.add_handler(CommandHandler("rekomendasi", rekomendasi))
    app.add_handler(CommandHandler("akumulasi", akumulasi))
    app.add_handler(CommandHandler("swing_cepat", swing_cepat))
    app.add_handler(CommandHandler("scalping", scalping))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_error_handler(error_handler)
    print(f"🤖 Bot v{BOT_CREATOR['version']} by {BOT_CREATOR['name']} berjalan...")
    print("Commands: /start, /about, /scan, /rekomendasi, /akumulasi, /swing_cepat, /scalping")
    app.run_polling()

def run_bot():
    main()

if __name__ == "__main__":
    main()
