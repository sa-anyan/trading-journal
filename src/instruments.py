import re

FOREX_MAJORS = {
    "EURUSD","GBPUSD","USDJPY","USDCHF","USDCAD","AUDUSD","NZDUSD"
}
METALS = {"XAUUSD": "Gold", "XAGUSD": "Silver"}
INDICES = {
    "NAS100":"US Tech 100","US100":"US Tech 100","NDX":"Nasdaq 100",
    "SPX500":"S&P 500","US500":"S&P 500","SPX":"S&P 500",
    "DJI":"Dow Jones","US30":"Dow Jones",
    "GER40":"DAX","DE40":"DAX","UK100":"FTSE 100"
}
CRYPTO = {"BTCUSD":"Bitcoin","ETHUSD":"Ethereum","SOLUSD":"Solana"}
ENERGY = {"USOIL":"WTI Crude","UKOIL":"Brent Crude","WTICOUSD":"WTI Crude","BCOUSD":"Brent Crude"}

def clean_symbol(symbol: str) -> str:
    s = (symbol or "").upper().strip()
    if ":" in s:
        s = s.split(":")[-1]
    return re.sub(r"[^A-Z0-9]", "", s)

def classify_instrument(symbol: str):
    s = clean_symbol(symbol)
    if s in METALS:
        return {"asset_class":"Commodities","group_name":"Metals","instrument_name":METALS[s]}
    if s in ENERGY:
        return {"asset_class":"Commodities","group_name":"Energy","instrument_name":ENERGY[s]}
    if s in INDICES:
        return {"asset_class":"Indices","group_name":"Equity Indices","instrument_name":INDICES[s]}
    if s in CRYPTO or s.endswith("USDT"):
        return {"asset_class":"Crypto","group_name":"Crypto","instrument_name":CRYPTO.get(s, s)}
    if s in FOREX_MAJORS or (len(s) == 6 and s.isalpha()):
        quote = s[3:] if len(s) == 6 else ""
        group = "Major FX" if s in FOREX_MAJORS else (f"{quote}-quoted FX" if quote else "Forex")
        return {"asset_class":"Forex","group_name":group,"instrument_name":s}
    return {"asset_class":"Other","group_name":"Unclassified","instrument_name":s or "UNKNOWN"}
