import yfinance as yf
import pandas as pd
import numpy as np
import warnings
from issi_symbols import ISSI_BATCHES

# Ignore yfinance warnings
warnings.filterwarnings("ignore", category=UserWarning, module="yfinance")

# ===============================
# Clean Symbol
# ===============================
def clean_symbol(symbol: str):
    return symbol.replace(".JK", "").replace(".jk", "")

# ===============================
# Stochastic (10,5,5)
# ===============================
def stochastic(df, k_period=10, d_period=5, smooth_k=5):
    low_min =  df["Low"].rolling(k_period).min()
    high_max = df["High"].rolling(k_period).max()
    k_fast = 100 * (df["Close"] - low_min) / (high_max - low_min)
    k_smooth = k_fast.rolling(smooth_k).mean()
    d_line = k_smooth.rolling(d_period).mean()
    return k_smooth, d_line

# ===============================
# RSI
# ===============================
def calculate_rsi(df, period=14):
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# ===============================
# MA5
# ===============================
def calculate_ma5(df):
    return df['Close'].rolling(5).mean()

# ===============================
# 1 Day Price Return
# ===============================
def calculate_1day_return(df):
    return df['Close'].pct_change() * 100

# =====================================================
# Fibonacci Levels (untuk /akumulasi)
# =====================================================
def get_fib_levels(df):
    try:
        high_val = df['High'].max()
        low_val = df['Low'].min()
        
        if hasattr(high_val, 'iloc'):
            high = float(high_val.iloc[0])
        elif hasattr(high_val, 'item'):
            high = float(high_val.item())
        else:
            high = float(high_val)
            
        if hasattr(low_val, 'iloc'):
            low = float(low_val.iloc[0])
        elif hasattr(low_val, 'item'):
            low = float(low_val.item())
        else:
            low = float(low_val)
        
        range_price = high - low
        fib_786 = round(high - (range_price * 0.786), 2)
        fib_618 = round(high - (range_price * 0.618), 2)
        tp_21 = round(high + (range_price * 0.21), 2)
        
        return {
            "fib_786": fib_786,
            "fib_618": fib_618,
            "tp_21": tp_21,
            "high": high,
            "low": low
        }
    except Exception as e:
        print(f"Error calculating Fibonacci: {e}")
        return None

# ===============================
# Ambil info saham (Daily) - UNTUK /akumulasi
# ===============================
def get_stock_info_fib(symbol, period="3mo", interval="1d"):
    try:
        df = yf.download(symbol, period=period, interval=interval, progress=False)

        if df.empty:
            return None

        df["K"], df["D"] = stochastic(df)
        
        fib_levels = get_fib_levels(df)
        
        if not fib_levels:
            return None

        last = df.iloc[-1]
        
        close_price = float(last["Close"].iloc[0]) if hasattr(last["Close"], 'iloc') else float(last["Close"])
        
        volume_val = last["Volume"]
        if hasattr(volume_val, 'iloc'):
            volume = int(volume_val.iloc[0]) if not pd.isna(volume_val.iloc[0]) else 0
        else:
            volume = int(volume_val) if not pd.isna(volume_val) else 0
            
        k_val = last["K"]
        if hasattr(k_val, 'iloc'):
            stoch_k = float(k_val.iloc[0]) if not pd.isna(k_val.iloc[0]) else 50
        else:
            stoch_k = float(k_val) if not pd.isna(k_val) else 50
            
        d_val = last["D"]
        if hasattr(d_val, 'iloc'):
            stoch_d = float(d_val.iloc[0]) if not pd.isna(d_val.iloc[0]) else 50
        else:
            stoch_d = float(d_val) if not pd.isna(d_val) else 50
        
        value = close_price * volume
        
        fib_786 = fib_levels['fib_786']
        fib_618 = fib_levels['fib_618']
        tp_21 = fib_levels['tp_21']
        
        harga_diatas_618 = close_price > fib_618
        harga_dibawah_786 = close_price < fib_786
        di_area_akumulasi = harga_diatas_618 and harga_dibawah_786
        
        tp = tp_21
        gain_tp = ((tp - close_price) / close_price) * 100 if tp > close_price else 0

        return {
            "symbol": symbol,
            "clean": clean_symbol(symbol),
            "close": round(close_price, 2),
            "volume": volume,
            "value": int(value),
            "stoch_k": round(stoch_k, 2),
            "stoch_d": round(stoch_d, 2),
            "fib_786": fib_786,
            "fib_618": fib_618,
            "tp_21": tp_21,
            "high": fib_levels['high'],
            "low": fib_levels['low'],
            "tp": round(tp, 2),
            "gain_tp": round(gain_tp, 2),
            "di_area_akumulasi": di_area_akumulasi,
            "stoch_oversold": stoch_k < 30 and stoch_d < 30,
        }

    except Exception as e:
        print(symbol, "error (Fibonacci):", e)
        return None

# ===============================
# Ambil info saham (Daily) - UNTUK /rekomendasi
# ===============================
def get_stock_info(symbol, period="6mo", interval="1d"):
    try:
        df = yf.download(symbol, period=period, interval=interval, progress=False)

        if df.empty:
            return None

        df["MA50"] = df["Close"].rolling(50).mean()
        df["K"], df["D"] = stochastic(df)

        last = df.iloc[-1]
        
        close_price = float(last["Close"].iloc[0]) if hasattr(last["Close"], 'iloc') else float(last["Close"])
        
        volume_val = last["Volume"]
        if hasattr(volume_val, 'iloc'):
            volume = int(volume_val.iloc[0]) if not pd.isna(volume_val.iloc[0]) else 0
        else:
            volume = int(volume_val) if not pd.isna(volume_val) else 0
            
        ma50_val = last["MA50"]
        if hasattr(ma50_val, 'iloc'):
            ma50 = float(ma50_val.iloc[0]) if not pd.isna(ma50_val.iloc[0]) else 0
        else:
            ma50 = float(ma50_val) if not pd.isna(ma50_val) else 0
            
        k_val = last["K"]
        if hasattr(k_val, 'iloc'):
            stoch_k = float(k_val.iloc[0]) if not pd.isna(k_val.iloc[0]) else 50
        else:
            stoch_k = float(k_val) if not pd.isna(k_val) else 50
            
        d_val = last["D"]
        if hasattr(d_val, 'iloc'):
            stoch_d = float(d_val.iloc[0]) if not pd.isna(d_val.iloc[0]) else 50
        else:
            stoch_d = float(d_val) if not pd.isna(d_val) else 50
            
        value = close_price * volume

        return {
            "symbol": symbol,
            "clean": clean_symbol(symbol),
            "close": round(close_price, 2),
            "ma50": round(ma50, 2),
            "stoch_k": round(stoch_k, 2),
            "stoch_d": round(stoch_d, 2),
            "volume": volume,
            "value": int(value),
            "above_ma50": close_price > ma50,
            "volume_ok": volume > 1000000,
            "value_ok": value > 3000000000,
            "stoch_oversold": stoch_k < 30 and stoch_d < 30,
        }

    except Exception as e:
        print(symbol, "error:", e)
        return None

# ===============================
# Ambil info saham (4H - untuk swing cepat)
# ===============================
def get_stock_info_4h(symbol, period="2mo"):
    try:
        df = yf.download(symbol, period=period, interval="1h", progress=False)
        
        if df.empty:
            return None
        
        df_4h = df.iloc[::4].copy()
        
        if df_4h.empty:
            return None
        
        df_4h["MA50"] = df_4h["Close"].rolling(50).mean()
        df_4h["K"], df_4h["D"] = stochastic(df_4h)
        
        last = df_4h.iloc[-1]
        
        close_price = float(last["Close"].iloc[0]) if hasattr(last["Close"], 'iloc') else float(last["Close"])
        
        volume_val = last["Volume"]
        if hasattr(volume_val, 'iloc'):
            volume = int(volume_val.iloc[0]) if not pd.isna(volume_val.iloc[0]) else 0
        else:
            volume = int(volume_val) if not pd.isna(volume_val) else 0
            
        ma50_val = last["MA50"]
        if hasattr(ma50_val, 'iloc'):
            ma50 = float(ma50_val.iloc[0]) if not pd.isna(ma50_val.iloc[0]) else 0
        else:
            ma50 = float(ma50_val) if not pd.isna(ma50_val) else 0
            
        k_val = last["K"]
        if hasattr(k_val, 'iloc'):
            stoch_k = float(k_val.iloc[0]) if not pd.isna(k_val.iloc[0]) else 50
        else:
            stoch_k = float(k_val) if not pd.isna(k_val) else 50
            
        d_val = last["D"]
        if hasattr(d_val, 'iloc'):
            stoch_d = float(d_val.iloc[0]) if not pd.isna(d_val.iloc[0]) else 50
        else:
            stoch_d = float(d_val) if not pd.isna(d_val) else 50
            
        value = close_price * volume
        
        return {
            "symbol": symbol,
            "clean": clean_symbol(symbol),
            "close": round(close_price, 2),
            "ma50": round(ma50, 2),
            "stoch_k": round(stoch_k, 2),
            "stoch_d": round(stoch_d, 2),
            "volume": volume,
            "value": int(value),
            "above_ma50": close_price > ma50,
            "volume_ok": volume > 300000,
            "value_ok": value > 300000000,
            "stoch_oversold": stoch_k < 30 and stoch_d < 30,
        }
        
    except Exception as e:
        print(symbol, "error (4H):", e)
        return None

# ===============================
# Ambil info saham (Daily) - UNTUK SCALPING (Tanpa Stochastic)
# ===============================
def get_stock_info_scalping(symbol, period="3mo", interval="1d"):
    try:
        df = yf.download(symbol, period=period, interval=interval, progress=False)
        
        if df.empty:
            return None
        
        # Calculate indicators
        df["MA5"] = calculate_ma5(df)
        df["RSI"] = calculate_rsi(df)
        df["1day_return"] = calculate_1day_return(df)
        
        last = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else last
        
        close_price = float(last["Close"].iloc[0]) if hasattr(last["Close"], 'iloc') else float(last["Close"])
        
        volume_val = last["Volume"]
        if hasattr(volume_val, 'iloc'):
            volume = int(volume_val.iloc[0]) if not pd.isna(volume_val.iloc[0]) else 0
        else:
            volume = int(volume_val) if not pd.isna(volume_val) else 0
            
        ma5_val = last["MA5"]
        if hasattr(ma5_val, 'iloc'):
            ma5 = float(ma5_val.iloc[0]) if not pd.isna(ma5_val.iloc[0]) else 0
        else:
            ma5 = float(ma5_val) if not pd.isna(ma5_val) else 0
            
        rsi_val = last["RSI"]
        if hasattr(rsi_val, 'iloc'):
            rsi = float(rsi_val.iloc[0]) if not pd.isna(rsi_val.iloc[0]) else 50
        else:
            rsi = float(rsi_val) if not pd.isna(rsi_val) else 50
            
        return_val = last["1day_return"]
        if hasattr(return_val, 'iloc'):
            daily_return = float(return_val.iloc[0]) if not pd.isna(return_val.iloc[0]) else 0
        else:
            daily_return = float(return_val) if not pd.isna(return_val) else 0
            
        value = close_price * volume
        
        # New filters for scalping (without stochastic)
        above_ma5_1 = close_price > (ma5 + 1)  # Harga lebih dari 1 dari MA5
        volume_ok_new = volume > 500000  # Volume > 500rb
        value_ok_new = value > 500000000  # Value > 500jt
        rsi_ok = rsi > 45  # RSI > 45
        
        return {
            "symbol": symbol,
            "clean": clean_symbol(symbol),
            "close": round(close_price, 2),
            "volume": volume,
            "value": int(value),
            "ma5": round(ma5, 2),
            "rsi": round(rsi, 2),
            "daily_return": round(daily_return, 2),
            "above_ma5_1": above_ma5_1,
            "volume_ok": volume_ok_new,
            "value_ok": value_ok_new,
            "rsi_ok": rsi_ok,
            "timeframe": "Daily"
        }
        
    except Exception as e:
        print(symbol, "error (Scalping Daily):", e)
        return None

# ===============================
# Format Output
# ===============================
def format_output(data):
    if not data:
        return "❌ Data tidak ditemukan"

    value_fmt = f"{data['value']:,}".replace(",", ".")
    status_ma50 = "✅" if data['above_ma50'] else "❌"
    status_volume = "✅" if data['volume_ok'] else "❌"
    status_value = "✅" if data['value_ok'] else "❌"
    status_stoch = "✅" if data['stoch_oversold'] else "❌"

    return (
        f"╔══════════════════════╗\n"
        f"🎯 {data['symbol']}\n"
        f"╠══════════════════════╣\n"
        f"💰 Harga   : {data['close']}\n"
        f"📉 MA50    : {data['ma50']}\n"
        f"📊 Stoch K : {data['stoch_k']}\n"
        f"📊 Stoch D : {data['stoch_d']}\n"
        f"📊 Volume  : {data['volume']:,}\n"
        f"💵 Value   : Rp {value_fmt}\n"
        f"🏷 Filter Status:\n"
        f"  {status_stoch} Stoch K,D < 15: {data['stoch_k']:.1f}, {data['stoch_d']:.1f}\n"
        f"  {status_ma50} Harga > MA50: {data['close']} > {data['ma50']}\n"
        f"  {status_volume} Volume > 1jt: {data['volume']:,} > 1,000,000\n"
        f"  {status_value} Value > 3M: Rp {value_fmt} > 3.000.000.000\n"
        f"📈 Chart   : https://stockbit.com/symbol/{data['clean']}?chart=1\n"
        f"╚══════════════════════╝"
    )

def format_output_4h(data):
    if not data:
        return "❌ Data tidak ditemukan"

    value_fmt = f"{data['value']:,}".replace(",", ".")
    status_ma50 = "✅" if data['above_ma50'] else "❌"
    status_volume = "✅" if data['volume_ok'] else "❌"
    status_value = "✅" if data['value_ok'] else "❌"
    status_stoch = "✅" if data['stoch_oversold'] else "❌"

    return (
        f"╔══════════════════════╗\n"
        f"⚡ {data['symbol']} (SWING CEPAT 4H)\n"
        f"╠══════════════════════╣\n"
        f"💰 Harga   : {data['close']}\n"
        f"📉 MA50    : {data['ma50']}\n"
        f"📊 Stoch K : {data['stoch_k']}\n"
        f"📊 Stoch D : {data['stoch_d']}\n"
        f"📊 Volume  : {data['volume']:,}\n"
        f"💵 Value   : Rp {value_fmt}\n"
        f"🏷 Filter Status (4H):\n"
        f"  {status_stoch} Stoch K,D < 15: {data['stoch_k']:.1f}, {data['stoch_d']:.1f}\n"
        f"  {status_ma50} Harga > MA50: {data['close']} > {data['ma50']}\n"
        f"  {status_volume} Volume > 300rb: {data['volume']:,} > 300,000\n"
        f"  {status_value} Value > 300jt: Rp {value_fmt} > 300,000,000\n"
        f"📈 Chart   : https://stockbit.com/symbol/{data['clean']}?chart=1\n"
        f"╚══════════════════════╝"
    )

def format_output_scalping(data):
    if not data:
        return "❌ Data tidak ditemukan"

    value_fmt = f"{data['value']:,}".replace(",", ".")
    status_volume = "✅" if data['volume_ok'] else "❌"
    status_value = "✅" if data['value_ok'] else "❌"
    status_ma5 = "✅" if data['above_ma5_1'] else "❌"
    status_rsi = "✅" if data['rsi_ok'] else "❌"
    
    # Color for daily return
    return_color = "🟢" if data['daily_return'] > 0 else "🔴" if data['daily_return'] < 0 else "⚪"
    return_sign = "+" if data['daily_return'] > 0 else ""

    return (
        f"╔══════════════════════╗\n"
        f"🎯 {data['symbol']} (SCALPING DAILY)\n"
        f"╠══════════════════════╣\n"
        f"💰 Harga     : {data['close']}\n"
        f"📈 1D Return : {return_color} {return_sign}{data['daily_return']}%\n"
        f"📊 MA5       : {data['ma5']}\n"
        f"📊 RSI       : {data['rsi']}\n"
        f"📊 Volume    : {data['volume']:,}\n"
        f"💵 Value     : Rp {value_fmt}\n"
        f"🏷 Filter Status:\n"
        f"  {status_ma5} Harga > MA5+1: {data['close']} > {data['ma5']+1:.2f}\n"
        f"  {status_volume} Volume > 500rb: {data['volume']:,} > 500,000\n"
        f"  {status_value} Value > 500jt: Rp {value_fmt} > 500,000,000\n"
        f"  {status_rsi} RSI > 45: {data['rsi']} > 45\n"
        f"📈 Chart   : https://stockbit.com/symbol/{data['clean']}?chart=1\n"
        f"╚══════════════════════╝"
    )

def format_output_akumulasi(data):
    if not data:
        return "❌ Data tidak ditemukan"

    value_fmt = f"{data['value']:,}".replace(",", ".")
    status_area = "✅" if data['di_area_akumulasi'] else "❌"
    status_stoch = "✅" if data['stoch_oversold'] else "❌"

    area_color = "🟢" if data['di_area_akumulasi'] else "⚪"
    area_text = f"{data['fib_618']} - {data['fib_786']}"

    return (
        f"╔══════════════════════╗\n"
        f"📈 {data['symbol']} (AKUMULASI)\n"
        f"╠══════════════════════╣\n"
        f"💰 Harga Saat Ini : {data['close']}\n"
        f"📊 Fibonacci Levels (3mo):\n"
        f"  🟣 TP +21%   : {data['tp_21']}\n"
        f"  🔴 78.6%     : {data['fib_786']}\n"
        f"  🟡 61.8%     : {data['fib_618']}\n"
        f"  ⚪ Low       : {data['low']}\n\n"
        f"📍 Area Akumulasi: {area_color} {area_text}\n\n"
        f"🎯 Target Price:\n"
        f"  TP (+21%): {data['tp']} (Gain: +{data['gain_tp']}%)\n\n"
        f"📊 Stoch K : {data['stoch_k']}\n"
        f"📊 Stoch D : {data['stoch_d']}\n"
        f"📊 Volume  : {data['volume']:,}\n"
        f"💵 Value   : Rp {value_fmt}\n\n"
        f"🏷 Filter Status:\n"
        f"  {status_area} Area Akumulasi ({area_text})\n"
        f"  {status_stoch} Stoch K,D < 30: {data['stoch_k']:.1f}, {data['stoch_d']:.1f}\n"
        f"📈 Chart   : https://stockbit.com/symbol/{data['clean']}?chart=1\n"
        f"╚══════════════════════╝"
    )

# ===============================
# Filter Functions
# ===============================
def filter_scalping(info):
    if not info:
        return False
    return (info.get("above_ma5_1", False) and    # Harga > MA5 + 1
            info.get("volume_ok", False) and       # Volume > 500rb
            info.get("value_ok", False) and        # Value > 500jt
            info.get("rsi_ok", False))             # RSI > 45

def filter_rekomendasi_stoch(info):
    if not info:
        return False
    return info.get("stoch_oversold", False) and info.get("volume_ok", False) and info.get("value_ok", False)

def filter_akumulasi(info):
    if not info:
        return False
    return (info.get("di_area_akumulasi", False) and 
            info.get("stoch_oversold", False))

# ===============================
# Search Functions
# ===============================
def cari_rekomendasi_stoch(symbols):
    results = []
    for sym in symbols:
        info = get_stock_info(sym)
        if info and filter_rekomendasi_stoch(info):
            results.append(info)
    results.sort(key=lambda x: x.get("stoch_k", 0))
    return results

def cari_akumulasi(symbols):
    results = []
    for sym in symbols:
        info = get_stock_info_fib(sym, period="3mo", interval="1d")
        if info and filter_akumulasi(info):
            results.append(info)
    results.sort(key=lambda x: abs(x.get("close", 0) - x.get("fib_618", 0)))
    return results

def cari_rekomendasi_swing_cepat(symbols):
    results = []
    for sym in symbols:
        info = get_stock_info_4h(sym)
        if info and filter_rekomendasi_stoch(info):
            results.append(info)
    results.sort(key=lambda x: x.get("stoch_k", 0))
    return results

def cari_rekomendasi_scalping(symbols):
    results = []
    for sym in symbols:
        info = get_stock_info_scalping(sym)
        if info and filter_scalping(info):
            results.append(info)
    results.sort(key=lambda x: x.get("daily_return", 0), reverse=True)  # Sort by daily return tertinggi
    return results
