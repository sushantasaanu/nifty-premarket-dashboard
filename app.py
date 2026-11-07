import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo

st.set_page_config(page_title="Nifty Pre-Market Intelligence", page_icon="📊", layout="centered")

IST = ZoneInfo("Asia/Kolkata")

st.title("📊 Nifty 50 Pre-Market Intelligence")
st.caption("Educational market-context dashboard • Dashboard only • No trade signals")

st.warning(
    "यह prototype delayed/last-available public market data दिखाता है। "
    "यह real-time exchange feed नहीं है और Nifty की अगली दिशा की गारंटी नहीं देता। "
    "इसे trading entry, options buying/selling या futures decisions के लिए अकेले इस्तेमाल न करें।"
)

SYMBOLS = {
    "Nifty 50": "^NSEI",
    "India VIX": "^INDIAVIX",
    "S&P 500": "^GSPC",
    "Nasdaq Composite": "^IXIC",
    "Nikkei 225": "^N225",
    "Hang Seng": "^HSI",
    "USD/INR": "INR=X",
}

@st.cache_data(ttl=300, show_spinner=False)
def get_history(symbol):
    # Yahoo Finance access through yfinance is unofficial; suitable only for a prototype.
    df = yf.Ticker(symbol).history(period="5d", interval="1d", auto_adjust=False)
    if df is None or df.empty:
        return None
    df = df.dropna(subset=["Close"])
    return df

def last_and_change(df):
    if df is None or len(df) < 1:
        return None, None, None
    last = float(df["Close"].iloc[-1])
    prev = float(df["Close"].iloc[-2]) if len(df) >= 2 else None
    pct = ((last / prev) - 1) * 100 if prev else None
    stamp = df.index[-1]
    return last, pct, stamp

def fmt(value, suffix=""):
    if value is None or pd.isna(value):
        return "Unavailable"
    return f"{value:,.2f}{suffix}"

now = datetime.now(IST)
st.write(f"**Dashboard checked:** {now.strftime('%d %b %Y, %I:%M:%S %p IST')}")
if st.button("↻ Refresh data", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

results = {}
with st.spinner("Latest available daily market data लाया जा रहा है..."):
    for name, symbol in SYMBOLS.items():
        try:
            df = get_history(symbol)
            value, pct, stamp = last_and_change(df)
            results[name] = {"value": value, "pct": pct, "stamp": stamp, "ok": value is not None}
        except Exception as exc:
            results[name] = {"value": None, "pct": None, "stamp": None, "ok": False, "error": str(exc)}

st.subheader("Market snapshot")
cols = st.columns(2)
for i, (name, item) in enumerate(results.items()):
    with cols[i % 2]:
        if item["ok"]:
            delta = f'{item["pct"]:+.2f}%' if item["pct"] is not None else "Change unavailable"
            st.metric(name, fmt(item["value"]), delta)
            st.caption(f'Last data bar: {item["stamp"]}')
        else:
            st.metric(name, "Unavailable")
            st.caption("Source did not return data")

st.subheader("Overnight global sentiment")
# Equal-weight context score. VIX and USD/INR are treated as risk-context indicators,
# not as deterministic predictors of Nifty direction.
score_parts = []
for name in ["S&P 500", "Nasdaq Composite", "Nikkei 225", "Hang Seng"]:
    p = results[name]["pct"]
    if p is not None:
        score_parts.append(p)

if score_parts:
    global_score = sum(score_parts) / len(score_parts)
    if global_score >= 0.35:
        label, explanation = "Positive global tone", "Major tracked equity indices are net positive."
    elif global_score <= -0.35:
        label, explanation = "Negative global tone", "Major tracked equity indices are net negative."
    else:
        label, explanation = "Mixed / neutral global tone", "Tracked equity indices do not show a strong common direction."
    st.metric("Equal-weight global equity context", f"{global_score:+.2f}%")
    st.info(f"**{label}.** {explanation}")
else:
    st.info("Global sentiment score उपलब्ध नहीं: पर्याप्त index data नहीं मिला।")

vix = results["India VIX"]["pct"]
if vix is not None:
    if vix > 3:
        st.warning("India VIX में पिछली उपलब्ध daily close से तेज बढ़त है: volatility context elevated हो सकता है.")
    elif vix < -3:
        st.success("India VIX पिछली उपलब्ध daily close से नीचे है: volatility context नरम हुआ है.")
    else:
        st.info("India VIX में बहुत बड़ा daily बदलाव नहीं दिख रहा.")
else:
    st.caption("India VIX risk context उपलब्ध नहीं है.")

st.subheader("What this does — and does not — mean")
st.markdown("""
- **Positive global tone** = overnight global equity context सकारात्मक है; यह Nifty gap-up की पुष्टि नहीं है।
- **Negative global tone** = overnight global equity context कमजोर है; यह Nifty gap-down की पुष्टि नहीं है।
- **Mixed / neutral** = संकेत एक दिशा में एकमत नहीं हैं।
- Nifty का actual opening gap, domestic news, Gift Nifty, institutional flows और market-specific events अलग से जाँचना ज़रूरी है।
""")

st.subheader("Data quality")
st.markdown("""
- Data provider: Yahoo Finance via `yfinance` (unofficial community library).
- Quotes may be delayed, incomplete, unavailable, or revised.
- Gift Nifty is intentionally not included because this free prototype has no verified, licensed live feed for it.
- Do not treat missing data as zero. Check the source timestamp before interpreting a value.
""")

st.caption("For education and market awareness only. Not investment advice. No buy/sell/entry/exit recommendations.")
