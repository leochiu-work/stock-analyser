import datetime
import os

import yfinance as yf
from dotenv import load_dotenv

load_dotenv()

tickers_raw = os.environ.get("TICKERS", "")
if not tickers_raw:
    raise ValueError("TICKERS is not set in .env")

tickers = [t.strip() for t in tickers_raw.split(",") if t.strip()]
today = datetime.date.today()

print(f"Fetching daily prices for: {', '.join(tickers)}")
print(f"Date: {today}\n")

df = yf.download(tickers, period="1d", interval="1d", auto_adjust=True)

if df.empty:
    print("No data returned. Market may be closed or tickers are invalid.")
else:
    print(df.to_string())

    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)
    for ticker in tickers:
        ticker_df = df.xs(ticker, axis=1, level="Ticker")
        csv_path = os.path.join(output_dir, f"{ticker}_{today}.csv")
        ticker_df.to_csv(csv_path)
        print(f"Saved {ticker} to {csv_path}")
