from sqlalchemy.orm import Session

from app.models.ticker import Ticker


class TickerRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_or_create(self, symbol: str) -> Ticker:
        ticker = self.db.query(Ticker).filter(Ticker.symbol == symbol).first()
        if ticker is None:
            ticker = Ticker(symbol=symbol)
            self.db.add(ticker)
            self.db.flush()
        return ticker

    def get_all(self) -> list[Ticker]:
        return self.db.query(Ticker).all()
