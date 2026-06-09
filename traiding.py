#from dotenv import load_dotenv  # pip install python-dotenv
#!pip install alpaca-py
import os
import pandas as pd
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetCalendarRequest
import sys
from alpaca.data import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime
    
API_KEY = os.getenv("API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")

if not API_KEY:
    raise ValueError("API_KEY saknas")

if not SECRET_KEY:
    raise ValueError("SECRET_KEY saknas")

print(f"API_KEY={API_KEY[:4]}...")

# Initialisera Alpaca's TradingClient i Paper-läge
trade_client = TradingClient(API_KEY, SECRET_KEY, paper=True)

# Valfritt: testa anslutning genom att hämta kontoinfo
account = trade_client.get_account()
print(account.buying_power)

symbols = ["AAPL", "MSFT", "GOOG"]  # exempel tickers
data_client = StockHistoricalDataClient(API_KEY, SECRET_KEY)

# Hämta senaste dagsbar (OHLCV) för varje symbol
end_date   = pd.Timestamp.today(tz="America/New_York").normalize()  # dagens datum (EST)



client = StockHistoricalDataClient(API_KEY, SECRET_KEY)

request = StockBarsRequest(
    symbol_or_symbols="MSFT",
    timeframe=TimeFrame.Day,
    start=datetime(2024, 1, 1),
    end=datetime(2024, 12, 31)
)

bars = client.get_stock_bars(request)

print(bars.df.head())



from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

# Förbered en marknadsorder (köper 10 aktier i ALFABET)
order_data = MarketOrderRequest(
    symbol="NVDA",
    qty=10,
    side=OrderSide.BUY,
    time_in_force=TimeInForce.DAY  # "DAY" = giltig tills dagens stängning
)
trade_client.submit_order(order_data=order_data)


import pandas as pd
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.data import StockHistoricalDataClient, TimeFrame

#API_KEY = "DIN-API-KEY"
#SECRET_KEY = "DIN-SECRET-KEY"
SYMBOLS = ["AAPL", "MSFT", "TSLA", "GOOG"]    # Dina utvalda tickers
MAX_ALLOCATION = 0.10                     # max 10% kapital per symbol

# 1. Initiera klients för handel & data
trade_client = TradingClient(API_KEY, SECRET_KEY, paper=True)
data_client = StockHistoricalDataClient(API_KEY, SECRET_KEY)

def is_trading_day(date):
    request = GetCalendarRequest(
        start=date.strftime("%Y-%m-%d"),
        end=date.strftime("%Y-%m-%d")
    )

    calendar = trade_client.get_calendar(filters=request)
    return len(calendar) > 0


# 2. Hämta dagens marknadsdatum
today = pd.Timestamp.now(tz="America/New_York").normalize()  # dagens datum (ET)
if not is_trading_day(today): 
    print("Marknaden är stängd idag")
    sys.exit()

# 3. Hämta senaste data för symbolerna (ex 100 dagars dagliga kurser)
request = StockBarsRequest(
    symbol_or_symbols=SYMBOLS,
    timeframe=TimeFrame.Day,
    start=today - pd.Timedelta(days=100),
    end=today
)

bars = data_client.get_stock_bars(request)

# 4. Hämta befintliga positioner för att veta vilka aktier som redan är köpta
positions = {pos.symbol: float(pos.qty) for pos in trade_client.get_all_positions()}

def check_signal_for_symbol(symbol, df):
    return "BUY"

# 5. Gå igenom varje symbol och bestäm action
for symbol in SYMBOLS:
    df = bars.df.loc[symbol]  # extrahera DataFrame för symbolen
    signal = check_signal_for_symbol(symbol, df)  # definiera enligt strategiregler
    if signal == "BUY":
        if symbol in positions:
            continue  # hoppa över om redan har position i symbolen
        # beräkna kvantitet baserat på max allokering
        last_price = df["close"].iloc[-1] 
        qty_to_buy = int((MAX_ALLOCATION * float(trade_client.get_account().buying_power)) // last_price)
        if qty_to_buy >= 1:
            order = MarketOrderRequest(symbol=symbol, qty=qty_to_buy,
                                       side=OrderSide.BUY, time_in_force=TimeInForce.DAY)
            trade_client.submit_order(order_data=order)
            print(f"Köper {qty_to_buy} st {symbol}")
    elif signal == "SELL":
        if symbol in positions and positions[symbol] > 0:
            # stäng hela positionen
            qty_to_sell = positions[symbol] 
            order = MarketOrderRequest(symbol=symbol, qty=qty_to_sell,
                                       side=OrderSide.SELL, time_in_force=TimeInForce.DAY)
            trade_client.submit_order(order_data=order)
            log(f"Säljer {qty_to_sell} st {symbol} @ market (stänger position)")