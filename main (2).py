from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import yfinance as yf
import requests
from datetime import datetime, timedelta

TOKEN = "8986723623:AAGE_OYm8D2s2yfWmQE-vYuHZN9H3BKUjMA"
TWELVE_TOKEN = "0642cfe3658b4e4186a379beacf02455"

PAIRS = {
    "SILVER": {"symbol": "SI=F", "name": "XAGUSD 🥈", "ar": "الفضة", "source": "yfinance"},
    "NASDAQ": {"symbol": "NQ=F", "name": "NASDAQ 📊", "ar": "ناسداك", "source": "yfinance"},
    "DOW_JONES": {"symbol": "YM=F", "name": "US30 📈", "ar": "داو جونز", "source": "yfinance"},
    "EURUSD": {"symbol": "EURUSD=X", "name": "EUR/USD 🇪🇺", "ar": "يورو/دولار", "source": "yfinance"},
    "USDJPY": {"symbol": "USDJPY=X", "name": "USD/JPY 🇯🇵", "ar": "دولار/ين", "source": "yfinance"},
    "GBPUSD": {"symbol": "GBPUSD=X", "name": "GBP/USD 🇬🇧", "ar": "جنيه/دولار", "source": "yfinance"},
    "BITCOIN": {"symbol": "BTC-USD", "name": "BITCOIN ₿", "ar": "بيتكوين", "source": "yfinance"},
    "OIL": {"symbol": "CL=F", "name": "USOIL 🛢️", "ar": "النفط", "source": "yfinance"}
}

def calculate_indicators(closes, highs, lows):
    """Helper function to calculate indicators"""
    if not closes or len(closes) < 14:
        return None
    
    c = closes[0]  # Current close
    hi = max(highs)
    lo = min(lows)
    
    # Calculate RSI
    deltas = [closes[i] - closes[i+1] for i in range(len(closes)-1)]
    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]
    
    avg_gain = sum(gains[-14:]) / 14 if len(gains) >= 14 else sum(gains) / len(gains)
    avg_loss = sum(losses[-14:]) / 14 if len(losses) >= 14 else sum(losses) / len(losses)
    
    if avg_loss == 0:
        rsi = 100.0
    else:
        rsi = round(100 - (100 / (1 + avg_gain / avg_loss)), 1)
    
    # Calculate SMA 20
    sma = sum(closes[:20]) / 20 if len(closes) >= 20 else sum(closes) / len(closes)
    trend = "🔼 صاعد" if c > sma else "🔽 هابط"
    
    # Pivot Points
    piv = round((hi + lo + c) / 3, 2)
    r1 = round(2 * piv - lo, 2)
    r2 = round(piv + (hi - lo), 2)
    r3 = round(hi + 2 * (piv - lo), 2)
    s1 = round(2 * piv - hi, 2)
    s2 = round(piv - (hi - lo), 2)
    s3 = round(lo - 2 * (hi - piv), 2)
    
    # Improved Signal Logic - Both BUY and SELL
    if rsi < 30 and c < sma:
        sig = "🟢 شراء قوي"
        entry = c
        tp = round(c * 1.008, 2)
        sl = round(c * 0.995, 2)
    elif rsi < 40 and c < sma:
        sig = "🟢 شراء"
        entry = c
        tp = round(c * 1.005, 2)
        sl = round(c * 0.997, 2)
    elif rsi > 70 and c > sma:
        sig = "🔴 بيع قوي"
        entry = c
        tp = round(c * 0.992, 2)
        sl = round(c * 1.005, 2)
    elif rsi > 60 and c > sma:
        sig = "🔴 بيع"
        entry = c
        tp = round(c * 0.995, 2)
        sl = round(c * 1.003, 2)
    else:
        sig = "⏸️ انتظار"
        entry = None
        tp = None
        sl = None
    
    return {
        "c": round(c, 2), "trend": trend, "rsi": rsi,
        "r1": r1, "r2": r2, "r3": r3,
        "s1": s1, "s2": s2, "s3": s3,
        "sig": sig, "entry": entry, "tp": tp, "sl": sl
    }

def get_gold_data_4h():
    """Fetch Gold data from Twelve Data API - 4H Timeframe"""
    try:
        url = f"https://api.twelvedata.com/time_series?symbol=GC/USD&interval=4h&outputsize=50&apikey={TWELVE_TOKEN}"
        response = requests.get(url).json()
        
        if "values" not in response or not response["values"]:
            return None
        
        values = response["values"]
        closes = [float(v['close']) for v in values]
        highs = [float(v['high']) for v in values]
        lows = [float(v['low']) for v in values]
        
        return calculate_indicators(closes, highs, lows)
    except Exception as e:
        print(f"Gold 4H Error: {e}")
        return None

def get_gold_data_1d():
    """Fetch Gold data from Twelve Data API - 1D Timeframe"""
    try:
        url = f"https://api.twelvedata.com/time_series?symbol=GC/USD&interval=1day&outputsize=30&apikey={TWELVE_TOKEN}"
        response = requests.get(url).json()
        
        if "values" not in response or not response["values"]:
            return None
        
        values = response["values"]
        closes = [float(v['close']) for v in values]
        highs = [float(v['high']) for v in values]
        lows = [float(v['low']) for v in values]
        
        return calculate_indicators(closes, highs, lows)
    except Exception as e:
        print(f"Gold 1D Error: {e}")
        return None

def get_data_yfinance(pair):
    """Fetch data from Yahoo Finance - 4H Timeframe"""
    try:
        h = yf.Ticker(PAIRS[pair]["symbol"]).history(period="3mo", interval="4h")
        if h.empty:
            return None
        
        closes = h['Close'].tolist()
        highs = h['High'].tolist()
        lows = h['Low'].tolist()
        
        return calculate_indicators(closes, highs, lows)
    except Exception as e:
        print(f"YFinance {pair} Error: {e}")
        return None

def kb():
    """Main keyboard"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌍 الكل", callback_data="ALL")],
        [InlineKeyboardButton("🥇 GOLD", callback_data="GOLD_CHOICE"),
         InlineKeyboardButton("🥈 SILVER", callback_data="SILVER")],
        [InlineKeyboardButton("📊 NASDAQ", callback_data="NASDAQ"),
         InlineKeyboardButton("📈 DOW JONES", callback_data="DOW_JONES")],
        [InlineKeyboardButton("🇪🇺 EUR/USD", callback_data="EURUSD"),
         InlineKeyboardButton("🇯🇵 USD/JPY", callback_data="USDJPY")],
        [InlineKeyboardButton("🇬🇧 GBP/USD", callback_data="GBPUSD"),
         InlineKeyboardButton("₿ BITCOIN", callback_data="BITCOIN")],
        [InlineKeyboardButton("🛢️ OIL", callback_data="OIL")]
    ])

def gold_timeframe_kb():
    """Gold timeframe selection keyboard"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Gold 1 Day", callback_data="GOLD_1D"),
         InlineKeyboardButton("⏱️ Gold 4 Hours", callback_data="GOLD_4H")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back")]
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

    if q.data == "GOLD_CHOICE":
        await q.edit_message_text(
            "🥇 اختر الإطار الزمني للذهب:\n\n"
            "📊 Daily - للتحليل طويل الأجل\n"
            "⏱️ 4 Hours - للتحليل قصير الأجل",
            reply_markup=gold_timeframe_kb()
        )
        return

    if q.data == "ALL":
        msg = "📊 ملخص الأسواق\n"
        msg += "━━━━━━━━━━━━━━━━\n"
        
        # Gold both timeframes
        gold_1d = get_gold_data_1d()
        gold_4h = get_gold_data_4h()
        if gold_1d:
            msg += f"🥇 GOLD 1D: {gold_1d['c']} {gold_1d['trend']}\n"
        if gold_4h:
            msg += f"🥇 GOLD 4H: {gold_4h['c']} {gold_4h['trend']}\n"
        
        # Other pairs
        for key in PAIRS:
            d = get_data_yfinance(key)
            if d:
                msg += f"{PAIRS[key]['name']}: {d['c']} {d['trend']}\n"
        
        await q.edit_message_text(
            msg,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 رجوع", callback_data="back")]
            ])
        )
        return

    # Handle Gold timeframes
    if q.data == "GOLD_1D":
        d = get_gold_data_1d()
        if not d:
            await q.edit_message_text("❌ خطأ - حاول مرة أخرى")
            return
        
        name = "XAUUSD 🥇 (1 Day)"
        timeframe_label = "📊 إطار زمني: يومي"
    elif q.data == "GOLD_4H":
        d = get_gold_data_4h()
        if not d:
            await q.edit_message_text("❌ خطأ - حاول مرة أخرى")
            return
        
        name = "XAUUSD 🥇 (4 Hours)"
        timeframe_label = "⏱️ إطار زمني: 4 ساعات"
    else:
        # Other pairs
        d = get_data_yfinance(q.data)
        if not d:
            await q.edit_message_text("❌ خطأ - حاول مرة أخرى")
            return
        
        name = PAIRS[q.data]['name']
        timeframe_label = "⏱️ إطار زمني: 4 ساعات"

    msg = (
        f"{'━'*20}\n"
        f"📌 {name}\n"
        f"{timeframe_label}\n"
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
            f"\n✅ الهدف TP: {d['tp']}"
            f"\n❌ وقف الخسارة SL: {d['sl']}"
        )

    msg += f"\n{'━'*20}"

    # Determine back button text
    if q.data == "GOLD_1D" or q.data == "GOLD_4H":
        back_data = "GOLD_CHOICE"
        back_text = "🔙 رجوع للإطارات"
    else:
        back_data = "back"
        back_text = "🔙 رجوع للقائمة"

    await q.edit_message_text(
        msg,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(back_text, callback_data=back_data)]
        ])
    )

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))
print("Bot is running!")
app.run_polling(drop_pending_updates=True)
