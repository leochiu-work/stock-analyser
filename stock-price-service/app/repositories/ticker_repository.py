from datetime import date

from sqlalchemy.orm import Session

from app.models.ticker import Ticker


class TickerRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_all(self) -> list[Ticker]:
        return self.db.query(Ticker).all()

    def get_or_create(self, symbol: str) -> Ticker:
        ticker = self.db.query(Ticker).filter(Ticker.symbol == symbol).first()
        if ticker is None:
            ticker = Ticker(symbol=symbol)
            self.db.add(ticker)
        return ticker

    def update_last_fetch_date(self, symbol: str, fetch_date: date) -> None:
        ticker = self.db.query(Ticker).filter(Ticker.symbol == symbol).first()
        if ticker:
            ticker.last_fetch_date = fetch_date
            self.db.commit()
