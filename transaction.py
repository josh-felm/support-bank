from datetime import date, datetime
import decimal
from pandas import Timestamp

class Transaction:
    PRINT_FORMAT = '{0:10} {1:10} {2:10} {3:30} {4:>6}'

    def __init__(self, date='', from_id='', to_id='', narrative='',amount=0) -> None:
        self.date        = date
        self.from_id     = from_id
        self.to_id       = to_id
        self.narrative   = narrative
        self.amount      = amount

    #NOTE can override print function in future
    def print_transaction(self):
        if type(self.date) == Timestamp:
            date_out = self.date.date()
        else:
            date_out = self.date
        print(self.PRINT_FORMAT.format(str(date_out), self.from_id, self.to_id, self.narrative, '£' + str(round(self.amount/100, 2))))