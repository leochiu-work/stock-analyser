from datetime import date

from sqlalchemy.orm import Session

from app.models.ticker import Ticker


class TickerRepository:
    def get_all(self, db: Session) -> list[Ticker]:
        return db.query(Ticker).all()

    def get_or_create(self, db: Session, symbol: str) -> Ticker:
        ticker = db.query(Ticker).filter(Ticker.symbol == symbol).first()
        if ticker is None:
            ticker = Ticker(symbol=symbol)
            db.add(ticker)
            db.commit()
            db.refresh(ticker)
        return ticker

    def update_last_fetch_date(self, db: Session, symbol: str, fetch_date: date) -> Ticker:
        ticker = db.query(Ticker).filter(Ticker.symbol == symbol).first()
        if ticker:
            ticker.last_fetch_date = fetch_date
            db.commit()
            db.refresh(ticker)
        return ticker
