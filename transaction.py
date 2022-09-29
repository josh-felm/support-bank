from datetime import date
import decimal

class Transaction:
    def __init__(self, date='', from_id='', to_id='', narrative='',amount=0) -> None:
        self.date        = date
        self.from_id     = from_id
        self.to_id       = to_id
        self.narrative   = narrative
        self.amount      = amount

    def print_transaction(self):
        print(f'date:{self.date}, from:{self.from_id}, to:{self.to_id}, narrative: {self.narrative}, amount:£{decimal.Decimal(self.amount)}')