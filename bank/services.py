import pickle
import tempfile
import os

from bank.repository import DatabaseRepository
from bank.models import Customer, Employee
from bank.exceptions import (
    AccountNotFoundError,
    InsufficientFundsError,
    InvalidFieldError,
    EmployeeNotFoundError,
    AuthenticationError,
    DuplicateEmployeeError,
)

TEMP_DIR = tempfile.gettempdir()
SESSION_CACHE = os.path.join(TEMP_DIR, "bank_sessions.pkl")


class AdminService:
    def __init__(self, repo: DatabaseRepository):
        self._repo = repo

    def authenticate(self, name: str, password: str) -> bool:
        if not self._repo.verify_admin(name, password):
            raise AuthenticationError("Admin")
        return True

    def check_admin(self, name: str, password: str) -> bool:
        return self._repo.verify_admin(name, password)

    def get_total_money(self) -> int:
        return self._repo.get_total_balance()


class EmployeeService:
    def __init__(self, repo: DatabaseRepository):
        self._repo = repo

    def authenticate(self, name: str, password: str) -> bool:
        if not self._repo.verify_employee(name, password):
            raise AuthenticationError("Employee")
        return True

    def check_employee(self, name: str, password: str) -> bool:
        return self._repo.verify_employee(name, password)

    def create_employee(self, name: str, password: str, salary: int, position: str) -> Employee:
        emp = Employee(name=name, password=password, salary=salary, position=position)
        self._repo.insert_employee(emp)
        return emp

    def get_all_employees(self) -> list[Employee]:
        return self._repo.get_all_employees()

    def get_employees_summary(self) -> list[tuple]:
        return self._repo.get_employees_summary()

    def find_employee(self, name: str) -> Employee:
        emp = self._repo.find_employee_by_name(name)
        if not emp:
            raise EmployeeNotFoundError(name)
        return emp

    def employee_exists(self, name: str) -> bool:
        return self._repo.employee_exists(name)

    def update_employee_name(self, new_name: str, current_name: str) -> None:
        self._repo.update_employee_field("name", new_name, current_name)

    def update_employee_password(self, new_password: str, name: str) -> None:
        self._repo.update_employee_field("pass", new_password, name)

    def update_employee_salary(self, new_salary: int, name: str) -> None:
        self._repo.update_employee_field("salary", new_salary, name)

    def update_employee_position(self, new_position: str, name: str) -> None:
        self._repo.update_employee_field("position", new_position, name)


class CustomerService:
    def __init__(self, repo: DatabaseRepository):
        self._repo = repo

    def create_customer(
        self, name: str, age: int, address: str, balance: int,
        acc_type: str, mobile_number: str
    ) -> int:
        acc_no = self._repo._get_next_acc_no()
        customer = Customer(
            acc_no=acc_no,
            name=name,
            age=int(age),
            address=address,
            balance=int(balance),
            account_type=acc_type,
            mobile_number=mobile_number,
        )
        self._repo.insert_customer(customer)
        self._repo.log_transaction(acc_no, "ACCOUNT_CREATED", int(balance), 0, int(balance))
        return acc_no

    def get_details(self, acc_no: int) -> tuple:
        customer = self._repo.get_customer(acc_no)
        if not customer:
            return None
        return customer.to_tuple()

    def get_detail(self, acc_no: int) -> tuple:
        return self._repo.get_customer_name_balance(acc_no)

    def account_exists(self, acc_no: int) -> bool:
        return self._repo.account_exists(acc_no)

    def add_balance(self, amount: int, acc_no: int) -> None:
        balance_before = self._repo.get_balance(acc_no)
        if balance_before is None:
            raise AccountNotFoundError(acc_no)
        amount = int(amount)
        self._repo.add_balance(amount, acc_no)
        self._repo.log_transaction(
            acc_no, "DEPOSIT", amount, balance_before, balance_before + amount
        )
        self._save_session_cache(acc_no, "deposit", amount)

    def deduct_balance(self, amount: int, acc_no: int) -> bool:
        balance_before = self._repo.get_balance(acc_no)
        if balance_before is None:
            raise AccountNotFoundError(acc_no)
        amount = int(amount)
        success = self._repo.deduct_balance(amount, acc_no)
        if success:
            self._repo.log_transaction(
                acc_no, "WITHDRAWAL", amount, balance_before, balance_before - amount
            )
        return success

    def check_balance(self, acc_no: int) -> int:
        bal = self._repo.get_balance(acc_no)
        return bal if bal is not None else 0

    def update_customer_name(self, new_name: str, acc_no: int) -> None:
        self._repo.update_customer_field("name", new_name, acc_no)

    def update_customer_age(self, new_age: int, acc_no: int) -> None:
        self._repo.update_customer_field("age", new_age, acc_no)

    def update_customer_address(self, new_address: str, acc_no: int) -> None:
        self._repo.update_customer_field("address", new_address, acc_no)

    def update_customer_mobile(self, new_mobile: str, acc_no: int) -> None:
        self._repo.update_customer_field("mobile_number", new_mobile, acc_no)

    def update_customer_acc_type(self, new_type: str, acc_no: int) -> None:
        self._repo.update_customer_field("account_type", new_type, acc_no)

    def list_all_customers(self) -> list[tuple]:
        return self._repo.get_all_customers_raw()

    def delete_account(self, acc_no: int) -> None:
        balance = self._repo.get_balance(acc_no)
        if balance is not None:
            self._repo.log_transaction(acc_no, "ACCOUNT_CLOSED", 0, balance, 0)
        self._repo.delete_customer(acc_no)

    def get_transaction_history(self, acc_no: int) -> list[tuple]:
        return self._repo.get_transaction_history(acc_no)

    def get_total_money(self) -> int:
        return self._repo.get_total_balance()

    def _save_session_cache(self, acc_no, operation, amount):
        try:
            if os.path.exists(SESSION_CACHE):
                with open(SESSION_CACHE, "rb") as f:
                    cache = pickle.load(f)
            else:
                cache = []
            cache.append({"acc_no": acc_no, "op": operation, "amount": amount})
            with open(SESSION_CACHE, "wb") as f:
                pickle.dump(cache, f)
        except:
            pass

    def load_session_cache(self):
        try:
            with open(SESSION_CACHE, "rb") as f:
                return pickle.load(f)
        except:
            return []
