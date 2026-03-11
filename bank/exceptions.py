class BankError(Exception):
    pass


class DatabaseConnectionError(BankError):
    def __init__(self, db_path: str, original_error: Exception):
        self.db_path = db_path
        self.original_error = original_error
        super().__init__(f"Failed to connect to database at {db_path}: {original_error}")


class TransactionRollbackError(BankError):
    pass


class AccountNotFoundError(BankError):
    def __init__(self, acc_no: int):
        self.acc_no = acc_no
        super().__init__(f"Account #{acc_no} not found")


class InsufficientFundsError(BankError):
    def __init__(self, acc_no: int, balance: int, amount: int):
        self.acc_no = acc_no
        self.balance = balance
        self.amount = amount
        super().__init__(
            f"Account #{acc_no}: insufficient funds "
            f"(balance={balance}, requested={amount})"
        )


class InvalidFieldError(BankError):
    def __init__(self, table: str, field: str):
        self.table = table
        self.field = field
        super().__init__(f"Invalid field '{field}' for table '{table}'")


class EmployeeNotFoundError(BankError):
    def __init__(self, name: str):
        self.name = name
        super().__init__(f"Employee '{name}' not found")


class AuthenticationError(BankError):
    def __init__(self, role: str):
        self.role = role
        super().__init__(f"{role} authentication failed")


class DuplicateEmployeeError(BankError):
    def __init__(self, name: str):
        self.name = name
        super().__init__(f"Employee '{name}' already exists")
