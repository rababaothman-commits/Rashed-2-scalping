from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import MetaTrader5 as mt5
import logging
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = "8456213095:AAHzAGUwWs1eSzbR_TeJdsb6FXshFJ-lfCY"

# EQUITI MT5 CREDENTIALS
MT5_LOGIN = 1140633
MT5_PASSWORD = "Cm2qVx-3"
MT5_SERVER = "EquitiBrokerageSC-Demo"

PAIRS = {
    "GOLD": {"symbol": "XAUUSD", "name": "XAUUSD 🥇", "ar": "الذهب"},
    "SILVER": {"symbol": "XAGUSD", "name": "XAGUSD 🥈", "ar": "الفضة"},
}

def connect_mt5():
    """Connect to MetaTrader 5"""
    try:
        if mt5.initialize(login=MT5_LOGIN, password=MT5_PASSWORD, server=MT5_SERVER):
            logger.info("✅ Connected to MT5")
            return True
        else:
            logger.error(f"❌ MT5 Connection Failed: {mt5.last_error()}")
            return False
    except Exception as e:
        logger.error(f"❌ MT5 Error: {str(e)}")
        return False

def calculate_rsi(closes, period=14):
    """Calculate RSI"""
    try:
        if len(closes) < period + 1:
            return 50.0
        
        delta = pd.Series(closes).diff()
        gain = delta.where(delta > 0, 0).rolling(window=period).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        last_rsi = float(rsi.iloc[-1])
        
        return last_rsi if not pd.isna(last_rsi) else 50.0
    except:
        return 50.0

def get_mt5_data(symbol):
    """Get data from MT5"""
    try:
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, 100)
        
        if rates is None or len(rates) < 14:
            logger.warning(f"⚠️ Not enough data for {symbol}")
            return None
        
        closes = [r['close'] for r in rates]
        highs = [r['high'] for r in rates]
        lows = [r['low'] for r in rates]
        
        current = round(closes[-1], 2)
        high = round(max(highs), 2)
        low = round(min(lows), 2)
        
        logger.info(f"✅ {symbol}: {current}")
        
        return {
            "closes": closes,
            "current": current,
            "high": high,
            "low": low
        }
    except Exception as e:
        logger.error(f"❌ {symbol} error: {e}")
        return None

def analyze(symbol_key):
    """Complete analysis"""
    try:
        symbol = PAIRS[symbol_key]["symbol"]
        
        # Get data
        data = get_mt5_data(symbol)
        if not data:
            return None
        
        c = data["current"]
        hi = data["high"]
        lo = data["low"]
        closes = data["closes"]
        
        # RSI
        rsi = calculate_rsi(closes, 14)
        
        # Trend
        sma = sum(closes[-20:]) / 20 if len(closes) >= 20 else c
        trend = "🔼 صاعد" if c > sma else "🔽 هابط"
        
        # Pivot
        piv = (hi + lo + c) / 3
        r1 = round(2 * piv - lo, 2)
        r2 = round(piv + (hi - lo), 2)
        r3 = round(hi + 2 * (piv - lo), 2)
        s1 = round(2 * piv - hi, 2)
        s2 = round(piv - (hi - lo), 2)
        s3 = round(lo - 2 * (hi - piv), 2)
        
        # Signal
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
        
        return {
            "c": c,
            "trend": trend,
            "rsi": round(rsi, 1),
            "r1": r1, "r2": r2, "r3": r3,
            "s1": s1, "s2": s2, "s3": s3,
            "sig": sig,
            "entry": entry,
            "tp": tp,
            "sl": sl
        }
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        return None

def kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🥇 GOLD", callback_data="GOLD"),
         InlineKeyboardButton("🥈 SILVER", callback_data="SILVER")],
        [InlineKeyboardButton("📊 ملخص", callback_data="SUMMARY")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not connect_mt5():
        await update.message.reply_text(
            "❌ خطأ في الاتصال\n"
            "تأكد من:\n"
            "1. تشغيل MT5\n"
            "2. بيانات صحيحة"
        )
        return
    
    await update.message.reply_text(
        "🤖 بوت الذهب والفضة\n"
        "📊 Equiti MT5\n"
        "✅ متصل\n\n"
        "اختر:",
        reply_markup=kb()
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "SUMMARY":
        gold = analyze("GOLD")
        silver = analyze("SILVER")
        
        msg = "📊 الملخص\n━━━━━━━━━━━━\n"
        if gold:
            msg += f"🥇 {gold['c']} {gold['trend']}\nRSI: {gold['rsi']} {gold['sig']}\n\n"
        else:
            msg += "🥇 ❌\n\n"
        if silver:
            msg += f"🥈 {silver['c']} {silver['trend']}\nRSI: {silver['rsi']} {silver['sig']}\n"
        else:
            msg += "🥈 ❌\n"
        msg += "━━━━━━━━━━━━"
        
        await q.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="back")]]))
        return

    if q.data == "back":
        await q.edit_message_text("🤖 بوت الذهب والفضة\n\nاختر:", reply_markup=kb())
        return

    d = analyze(q.data)
    if not d:
        await q.edit_message_text("❌ خطأ", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="back")]]))
        return

    name = PAIRS[q.data]['name']
    msg = (
        f"━━━━━━━━━━━━━━\n"
        f"{name}\n"
        f"━━━━━━━━━━━━━━\n\n"
        f"💰 {d['c']}\n"
        f"📈 {d['trend']}\n"
        f"⚡ RSI: {d['rsi']}\n\n"
        f"━━━━━━━━━━━━━━\n"
        f"🔴 R1: {d['r1']} | R2: {d['r2']} | R3: {d['r3']}\n"
        f"🟢 S1: {d['s1']} | S2: {d['s2']} | S3: {d['s3']}\n\n"
        f"━━━━━━━━━━━━━━\n"
        f"{d['sig']}\n"
    )
    
    if d['entry']:
        msg += f"\n💵 {d['entry']}\n🎯 {d['tp']}\n🛑 {d['sl']}"
    
    msg += "\n━━━━━━━━━━━━━━"
    
    await q.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="back")]]))

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    
    print("\n✅ MT5 GOLD & SILVER BOT\n")
    app.run_polling(drop_pending_updates=True)
