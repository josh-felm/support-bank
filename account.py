class Account:
    def __init__(self, name) -> None:
        self.account_id = name
        self.balance = 0
        self.transaction_history = []