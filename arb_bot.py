import streamlit as st
import requests
import pandas as pd
import random
import time

# ------------------------------------------------
#   إعدادات البوت
# ------------------------------------------------
MODE = "DEMO"    # DEMO = بدون API ، LIVE = يستخدم API

# في وضع LIVE ضع مفاتيحك هنا لاحقًا:
API_KEYS = {
    "binance": {"key": "", "secret": ""},
    "okx": {"key": "", "secret": ""},
    "bybit": {"key": "", "secret": ""},
    "bitget": {"key": "", "secret": ""},
    "bingx": {"key": "", "secret": ""},
}

# ------------------------------------------------
#   المحفظة الداخلية
# ------------------------------------------------
class Wallet:
    def __init__(self):
        self.balance = {
            "USDT": 10000,     # رصيد تجريبي
            "BTC": 0,
            "ETH": 0
        }

    def add(self, symbol, amount):
        self.balance[symbol] += amount

    def subtract(self, symbol, amount):
        if self.balance[symbol] >= amount:
            self.balance[symbol] -= amount
            return True
        return False

wallet = Wallet()

# ------------------------------------------------
#   أسعار أعلى 30 عملة
# ------------------------------------------------
def get_top_30():
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {"vs_currency": "usd", "order": "market_cap_desc", "per_page": 30, "page": 1}
        data = requests.get(url, params=params).json()
        df = pd.DataFrame(data)[["symbol", "name", "current_price", "market_cap", "price_change_percentage_24h"]]
        return df
    except:
        st.error("تعذر تحميل أعلى 30 عملة")
        return pd.DataFrame()

# ------------------------------------------------
#   جلب أسعار من المنصات (تجريبي بدون API)
# ------------------------------------------------
def demo_price(symbol):
    return round(random.uniform(10000, 60000), 2)

def get_prices(symbol):
    return {
        "Binance": demo_price(symbol),
        "OKX": demo_price(symbol),
        "Bybit": demo_price(symbol),
        "Bitget": demo_price(symbol),
        "BingX": demo_price(symbol),
    }

# ------------------------------------------------
#   إيجاد فرص الأرّبتراج
# ------------------------------------------------
def find_arbitrage(prices):
    min_ex = min(prices, key=prices.get)
    max_ex = max(prices, key=prices.get)
    diff = prices[max_ex] - prices[min_ex]
    percent = (diff / prices[min_ex]) * 100

    return min_ex, max_ex, diff, percent

# ------------------------------------------------
#   واجهة Streamlit
# ------------------------------------------------
st.set_page_config(page_title="Crypto Arbitrage Bot", layout="wide")
st.title("🚀 Crypto Arbitrage Bot — DEMO/LIVE")

st.sidebar.header("⚙️ الإعدادات")
mode = st.sidebar.selectbox("اختر الوضع:", ["DEMO", "LIVE"])
symbol = st.sidebar.selectbox("اختر العملة:", ["BTC/USDT", "ETH/USDT"])

st.sidebar.write("💳 **المحفظة الداخلية**")
st.sidebar.json(wallet.balance)

st.sidebar.write("🔌 **إضافة API (للوضع الحقيقي)**")
if mode == "LIVE":
    st.warning("ضع مفاتيح API داخل الملف مباشرة (API_KEYS)")

st.header("📊 أسعار أعلى 30 عملة في السوق")
df_top = get_top_30()
st.dataframe(df_top, use_container_width=True)

st.header("🔍 أسعار المنصات الخمس")
prices = get_prices(symbol)
st.json(prices)

min_ex, max_ex, diff, percent = find_arbitrage(prices)

st.subheader("💡 فرصة الأرّبتراج الحالية")
st.success(f"اشترِ من **{min_ex}** بسعر {prices[min_ex]} ‑ وبِع على **{max_ex}** بسعر {prices[max_ex]}")
st.info(f"الربح: {diff:.2f} USDT — نسبة: {percent:.2f}%")

st.header("🟢 تنفيذ الصفقة")
amount = st.number_input("الكمية (USDT):", min_value=10, value=100)

if st.button("تنفيذ العملية (تجريبية)"):
    if wallet.subtract("USDT", amount):
        buy_price = prices[min_ex]
        asset_amount = amount / buy_price
        wallet.add("BTC", asset_amount)
        st.success(f"تم الشراء من {min_ex} — BTC المضافة: {asset_amount}")
    else:
        st.error("رصيد غير كافٍ")

st.sidebar.write("🔄 تحديث يدوي للأسعار")
if st.sidebar.button("🔃 تحديث"):
    st.rerun()
