from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import finnhub
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = "8986723623:AAGlC1T8ZWEonOD58ChGBhRsEBdQ9nIp4Pc"
FINNHUB_API_KEY = "d8fn3b9r01qn443aqb4gd8fn3b9r01qn443aqb50"  # Get free at https://finnhub.io

PAIRS = {
    "GOLD": {"symbol": "GC=F", "name": "XAUUSD 🥇", "ar": "الذهب"},
    "SILVER": {"symbol": "SI=F", "name": "XAGUSD 🥈", "ar": "الفضة"},
    "NASDAQ": {"symbol": "^GSPC", "name": "NASDAQ 📊", "ar": "ناسداك"},
    "DOW_JONES": {"symbol": "^DJI", "name": "US30 📈", "ar": "داو جونز"},
    "EURUSD": {"symbol": "EURUSD", "name": "EUR/USD 🇪🇺", "ar": "يورو/دولار"},
    "USDJPY": {"symbol": "USDJPY", "name": "USD/JPY 🇯🇵", "ar": "دولار/ين"},
    "GBPUSD": {"symbol": "GBPUSD", "name": "GBP/USD 🇬🇧", "ar": "جنيه/دولار"},
    "BITCOIN": {"symbol": "BTC-USD", "name": "BITCOIN ₿", "ar": "بيتكوين"},
    "OIL": {"symbol": "CL=F", "name": "USOIL 🛢️", "ar": "النفط"}
}

def get_finnhub_data(symbol):
    """Fetch real-time data from Finnhub"""
    try:
        client = finnhub.Client(api_key=FINNHUB_API_KEY)
        
        # Get quote data
        quote = client.quote(symbol)
        
        if not quote or 'c' not in quote:
            logger.error(f"No data from Finnhub for {symbol}")
            return None
        
        c = float(quote['c'])  # Current price
        hi = float(quote['h'])  # High
        lo = float(quote['l'])  # Low
        o = float(quote['o'])   # Open
        
        logger.info(f"✅ Finnhub data for {symbol}: Price={c}, High={hi}, Low={lo}")
        
        return {
            "c": c,
            "h": hi,
            "l": lo,
            "o": o
        }
    except Exception as e:
        logger.error(f"Finnhub error for {symbol}: {str(e)}")
        return None

def calculate_rsi_simple(current_price, base_price):
    """Simple RSI estimation based on price deviation"""
    # Rough RSI calculation
    if current_price > base_price:
        # Uptrend = higher RSI
        change_percent = ((current_price - base_price) / base_price) * 100
        rsi = min(70 + (change_percent * 0.5), 100)
    else:
        # Downtrend = lower RSI
        change_percent = ((base_price - current_price) / base_price) * 100
        rsi = max(30 - (change_percent * 0.5), 0)
    
    return round(rsi, 1)

def get_data(pair, base_price=None):
    """Get complete trading analysis"""
    try:
        symbol = PAIRS[pair]["symbol"]
        logger.info(f"Fetching {pair} ({symbol})...")
        
        # Get real Finnhub data
        data = get_finnhub_data(symbol)
        if not data:
            return None
        
        c = data["c"]
        hi = data["h"]
        lo = data["l"]
        
        # Use provided base price or current as base
        if base_price is None:
            base_price = c
        
        trend = "🔼 صاعد" if c > base_price else "🔽 هابط"
        
        # Calculate RSI
        rsi = calculate_rsi_simple(c, base_price)
        
        # Pivot levels
        piv = (hi + lo + c) / 3
        r1 = round(2 * piv - lo, 2)
        r2 = round(piv + (hi - lo), 2)
        r3 = round(hi + 2 * (piv - lo), 2)
        s1 = round(2 * piv - hi, 2)
        s2 = round(piv - (hi - lo), 2)
        s3 = round(lo - 2 * (hi - piv), 2)
        
        # Signal based on RSI
        if rsi < 30:
            sig = "🟢 شراء قوي"
            entry = c
            tp = round(c * 1.02, 2)
            sl = round(c * 0.98, 2)
        elif rsi < 40:
            sig = "🟢 شراء"
            entry = c
            tp = round(c * 1.015, 2)
            sl = round(c * 0.985, 2)
        elif rsi > 70:
            sig = "🔴 بيع قوي"
            entry = c
            tp = round(c * 0.98, 2)
            sl = round(c * 1.02, 2)
        elif rsi > 60:
            sig = "🔴 بيع"
            entry = c
            tp = round(c * 0.985, 2)
            sl = round(c * 1.015, 2)
        else:
            sig = "⏸️ انتظار"
            entry = None
            tp = None
            sl = None
        
        logger.info(f"✅ {pair}: Price={c}, RSI={rsi}, Signal={sig}")
        
        return {
            "c": round(c, 2),
            "trend": trend,
            "rsi": rsi,
            "r1": r1,
            "r2": r2,
            "r3": r3,
            "s1": s1,
            "s2": s2,
            "s3": s3,
            "sig": sig,
            "entry": entry,
            "tp": tp,
            "sl": sl,
            "source": "📡 Finnhub Real-Time Data"
        }
    except Exception as e:
        logger.error(f"Error in get_data for {pair}: {e}")
        return None

def kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌍 الكل", callback_data="ALL")],
        [InlineKeyboardButton("🥇 GOLD", callback_data="GOLD"),
         InlineKeyboardButton("🥈 SILVER", callback_data="SILVER")],
        [InlineKeyboardButton("📊 NASDAQ", callback_data="NASDAQ"),
         InlineKeyboardButton("📈 DOW JONES", callback_data="DOW_JONES")],
        [InlineKeyboardButton("🇪🇺 EUR/USD", callback_data="EURUSD"),
         InlineKeyboardButton("🇯🇵 USD/JPY", callback_data="USDJPY")],
        [InlineKeyboardButton("🇬🇧 GBP/USD", callback_data="GBPUSD"),
         InlineKeyboardButton("₿ BITCOIN", callback_data="BITCOIN")],
        [InlineKeyboardButton("🛢️ OIL", callback_data="OIL")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if FINNHUB_API_KEY == "YOUR_FINNHUB_API_KEY":
        await update.message.reply_text(
            "⚠️ API KEY NOT SET!\n\n"
            "1. Get free key: https://finnhub.io/register\n"
            "2. Replace 'YOUR_FINNHUB_API_KEY' in code\n"
            "3. Redeploy bot"
        )
        return
    
    await update.message.reply_text(
        "🤖 بوت إشارات التداول الاحترافي\n"
        "✅ Finnhub Real-Time Edition\n\n"
        "اختر الزوج لعرض التحليل الكامل 👇",
        reply_markup=kb()
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "back":
        await q.edit_message_text(
            "🤖 بوت إشارات التداول الاحترافي\n\n"
            "اختر الزوج لعرض التحليل الكامل 👇",
            reply_markup=kb()
        )
        return

    if q.data == "ALL":
        msg = "📊 ملخص الأسواق\n"
        msg += "━━━━━━━━━━━━━━━━\n"
        count = 0
        for key in PAIRS:
            d = get_data(key)
            if d:
                msg += f"✅ {PAIRS[key]['name']}: {d['c']} {d['trend']}\n"
                count += 1
            else:
                msg += f"⏳ {PAIRS[key]['name']}\n"
        msg += f"━━━━━━━━━━━━━━━━\n{count}/9 متاح"
        await q.edit_message_text(
            msg,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 رجوع", callback_data="back")]
            ])
        )
        return

    d = get_data(q.data)
    if not d:
        await q.edit_message_text(
            "⏳ جاري جلب البيانات...\n"
            "❌ لم يتمكن من الاتصال\n"
            "حاول مرة أخرى",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 رجوع", callback_data="back")]
            ])
        )
        return

    name = PAIRS[q.data]['name']

    msg = (
        f"{'━'*20}\n"
        f"📌 {name}\n"
        f"{d['source']}\n"
        f"{'━'*20}\n\n"
        f"💰 السعر: {d['c']}\n"
        f"📈 الاتجاه: {d['trend']}\n"
        f"⚡ RSI: {d['rsi']}\n\n"
        f"{'━'*20}\n"
        f"🔴 المقاومات:\n"
        f"R1: {d['r1']}\n"
        f"R2: {d['r2']}\n"
        f"R3: {d['r3']}\n\n"
        f"🟢 الدعوم:\n"
        f"S1: {d['s1']}\n"
        f"S2: {d['s2']}\n"
        f"S3: {d['s3']}\n\n"
        f"{'━'*20}\n"
        f"🎯 الإشارة: {d['sig']}\n"
    )

    if d['entry']:
        msg += (
            f"\n💵 الدخول: {d['entry']}\n"
            f"🎯 الهدف: {d['tp']}\n"
            f"🛑 الخسارة: {d['sl']}"
        )

    msg += f"\n{'━'*20}"

    await q.edit_message_text(
        msg,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 رجوع", callback_data="back")]
        ])
    )

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))

print("\n" + "="*60)
print("✅ FINNHUB TRADING BOT - REAL-TIME DATA")
print("="*60 + "\n")

app.run_polling(drop_pending_updates=True)

