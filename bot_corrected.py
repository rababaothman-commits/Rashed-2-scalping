from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import yfinance as yf
import pandas as pd
import logging
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = "8456213095:AAHzAGUwWs1eSzbR_TeJdsb6FXshFJ-lfCY"

PAIRS = {
    "GOLD": {"symbol": "GC=F", "name": "XAUUSD 🥇", "ar": "الذهب"},
    "SILVER": {"symbol": "SI=F", "name": "XAGUSD 🥈", "ar": "الفضة"},
    "NASDAQ": {"symbol": "NQ=F", "name": "NASDAQ 📊", "ar": "ناسداك"},
    "DOW_JONES": {"symbol": "YM=F", "name": "US30 📈", "ar": "داو جونز"},
    "EURUSD": {"symbol": "EURUSD=X", "name": "EUR/USD 🇪🇺", "ar": "يورو/دولار"},
    "USDJPY": {"symbol": "USDJPY=X", "name": "USD/JPY 🇯🇵", "ar": "دولار/ين"},
    "GBPUSD": {"symbol": "GBPUSD=X", "name": "GBP/USD 🇬🇧", "ar": "جنيه/دولار"},
    "BITCOIN": {"symbol": "BTC-USD", "name": "BITCOIN ₿", "ar": "بيتكوين"},
    "OIL": {"symbol": "CL=F", "name": "USOIL 🛢️", "ar": "النفط"}
}

def calculate_rsi(data, period=14):
    """Calculate RSI safely"""
    try:
        delta = data.diff()
        gain = delta.where(delta > 0, 0).rolling(window=period).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi.iloc[-1]) if not np.isnan(rsi.iloc[-1]) else 50.0
    except Exception as e:
        logger.error(f"RSI calculation error: {e}")
        return 50.0

def get_data(pair):
    try:
        symbol = PAIRS[pair]["symbol"]
        logger.info(f"Fetching data for {pair} ({symbol})")
        
        h = yf.Ticker(symbol).history(period="60d", interval="1d")
        
        if h.empty or len(h) < 14:
            logger.warning(f"Insufficient data for {pair}")
            return None
        
        # Safe data extraction
        c = float(h['Close'].iloc[-1])
        hi = float(h['High'].max())
        lo = float(h['Low'].min())
        
        # Calculate RSI safely
        rsi = calculate_rsi(h['Close'], period=14)
        
        # Calculate SMA safely
        sma = float(h['Close'].rolling(20).mean().iloc[-1])
        trend = "🔼 صاعد" if c > sma else "🔽 هابط"
        
        # Pivot levels
        piv = (hi + lo + c) / 3
        r1 = 2 * piv - lo
        r2 = piv + (hi - lo)
        r3 = hi + 2 * (piv - lo)
        s1 = 2 * piv - hi
        s2 = piv - (hi - lo)
        s3 = lo - 2 * (hi - piv)
        
        # Signal generation with improved logic
        if rsi < 30:
            sig = "🟢 شراء قوي"
            entry = c
            tp = c * 1.01
            sl = c * 0.99
        elif rsi < 40:
            sig = "🟢 شراء"
            entry = c
            tp = c * 1.008
            sl = c * 0.992
        elif rsi > 70:
            sig = "🔴 بيع قوي"
            entry = c
            tp = c * 0.99
            sl = c * 1.01
        elif rsi > 60:
            sig = "🔴 بيع"
            entry = c
            tp = c * 0.992
            sl = c * 1.008
        else:
            sig = "⏸️ انتظار"
            entry = None
            tp = None
            sl = None
        
        logger.info(f"{pair} ✅ - RSI: {rsi:.1f}, Signal: {sig}")
        
        return {
            "c": round(c, 2), 
            "trend": trend, 
            "rsi": round(rsi, 1),
            "r1": round(r1, 2), 
            "r2": round(r2, 2), 
            "r3": round(r3, 2),
            "s1": round(s1, 2), 
            "s2": round(s2, 2), 
            "s3": round(s3, 2),
            "sig": sig, 
            "entry": round(entry, 2) if entry else None, 
            "tp": round(tp, 2) if tp else None, 
            "sl": round(sl, 2) if sl else None
        }
    except Exception as e:
        logger.error(f"Error fetching data for {pair}: {str(e)}")
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
    await update.message.reply_text(
        "🤖 بوت إشارات التداول الاحترافي\n\n"
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
        for key in PAIRS:
            d = get_data(key)
            if d:
                msg += f"{PAIRS[key]['name']}: {d['c']} {d['trend']}\n"
            else:
                msg += f"{PAIRS[key]['name']}: ❌\n"
        await q.edit_message_text(
            msg,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 رجوع", callback_data="back")]
            ])
        )
        return

    d = get_data(q.data)
    if not d:
        await q.edit_message_text("❌ خطأ في جلب البيانات - حاول مرة أخرى")
        return

    name = PAIRS[q.data]['name']

    msg = (
        f"{'━'*20}\n"
        f"📌 {name}\n"
        f"{'━'*20}\n\n"
        f"💰 السعر الحالي: {d['c']}\n"
        f"📈 الاتجاه: {d['trend']}\n"
        f"⚡ RSI: {d['rsi']}\n\n"
        f"{'━'*20}\n"
        f"🔴 المقاومات:\n"
        f"  R1: {d['r1']}\n"
        f"  R2: {d['r2']}\n"
        f"  R3: {d['r3']}\n\n"
        f"🟢 الدعوم:\n"
        f"  S1: {d['s1']}\n"
        f"  S2: {d['s2']}\n"
        f"  S3: {d['s3']}\n\n"
        f"{'━'*20}\n"
        f"🎯 الإشارة: {d['sig']}\n"
    )

    if d['entry']:
        msg += (
            f"\n💵 سعر الدخول: {d['entry']}"
            f"\n🎯 الهدف TP: {d['tp']}"
            f"\n🛑 وقف الخسارة SL: {d['sl']}"
        )

    msg += f"\n{'━'*20}"

    await q.edit_message_text(
        msg,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="back")]
        ])
    )

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))
print("✅ Trading Bot is running!")
app.run_polling(drop_pending_updates=True)
