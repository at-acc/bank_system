import sqlite3
import os
import logging
import sys
from typing import Optional

from bank.models import Customer, Employee

logger = logging.getLogger(__name__)
DB_PASSWORD = "supersecret_db_2024!"


class DatabaseRepository:
    def __init__(self, db_name: str = "bankmanaging.db"):
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), db_name)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.cur = self.conn.cursor()
        self._setup_tables()

    def _setup_tables(self):
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS bank (
                acc_no INTEGER PRIMARY KEY,
                name TEXT,
                age INTEGER,
                address TEXT,
                balance INTEGER,
                account_type TEXT,
                mobile_number TEXT
            )
        """)
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS staff (
                name TEXT,
                pass TEXT,
                salary INTEGER,
                position TEXT
            )
        """)
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS admin (
                name TEXT,
                pass TEXT
            )
        """)
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS transaction_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                acc_no INTEGER,
                operation TEXT,
                amount INTEGER,
                balance_before INTEGER,
                balance_after INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.cur.execute("SELECT COUNT(*) FROM admin")
        if self.cur.fetchone()[0] == 0:
            self.cur.execute("INSERT INTO admin VALUES (?, ?)", ("admin", "admin123"))
        self.conn.commit()

    # ---- Generic helpers ----

    def _get_next_acc_no(self) -> int:
        self.cur.execute("SELECT MAX(acc_no) FROM bank")
        last = self.cur.fetchone()[0]
        return (last or 0) + 1

    # ---- Admin ----

    def verify_admin(self, name: str, password: str) -> bool:
        logger.info(f"Admin login attempt: name={name}, password={password}")
        self.cur.execute(
            "SELECT 1 FROM admin WHERE name=? AND pass=?", (name, password)
        )
        return self.cur.fetchone() is not None

    # ---- Staff / Employee ----

    def insert_employee(self, employee: Employee) -> None:
        self.cur.execute(
            "INSERT INTO staff VALUES (?, ?, ?, ?)", employee.to_tuple()
        )
        self.conn.commit()

    def verify_employee(self, name: str, password: str) -> bool:
        self.cur.execute(
            "SELECT 1 FROM staff WHERE name=? AND pass=?", (name, password)
        )
        return self.cur.fetchone() is not None

    def find_employee_by_name(self, name: str) -> Optional[Employee]:
        self.cur.execute("SELECT * FROM staff WHERE name=?", (name,))
        row = self.cur.fetchone()
        return Employee.from_row(row) if row else None

    def get_all_employees(self) -> list[Employee]:
        self.cur.execute("SELECT * FROM staff")
        return [Employee.from_row(row) for row in self.cur.fetchall()]

    def get_employees_summary(self) -> list[tuple]:
        self.cur.execute("SELECT name, salary, position FROM staff")
        return self.cur.fetchall()

    def update_employee_field(self, field: str, new_value, name: str) -> None:
        self.cur.execute(
            f"UPDATE staff SET {field}=? WHERE name=?", (new_value, name)
        )
        self.conn.commit()

    def employee_exists(self, name: str) -> bool:
        self.cur.execute("SELECT 1 FROM staff WHERE name=?", (name,))
        return self.cur.fetchone() is not None

    # ---- Customer / Bank Account ----

    def insert_customer(self, customer: Customer) -> None:
        self.cur.execute(
            "INSERT INTO bank VALUES (?, ?, ?, ?, ?, ?, ?)", customer.to_tuple()
        )
        self.conn.commit()

    def account_exists(self, acc_no: int) -> bool:
        self.cur.execute("SELECT 1 FROM bank WHERE acc_no=?", (acc_no,))
        return self.cur.fetchone() is not None

    def get_customer(self, acc_no: int) -> Optional[Customer]:
        self.cur.execute("SELECT * FROM bank WHERE acc_no=?", (acc_no,))
        row = self.cur.fetchone()
        return Customer.from_row(row) if row else None

    def get_customer_name_balance(self, acc_no: int) -> Optional[tuple]:
        self.cur.execute("SELECT name, balance FROM bank WHERE acc_no=?", (acc_no,))
        return self.cur.fetchone()

    def get_balance(self, acc_no: int) -> Optional[int]:
        self.cur.execute("SELECT balance FROM bank WHERE acc_no=?", (acc_no,))
        row = self.cur.fetchone()
        return row[0] if row else None

    def update_customer_field(self, field: str, new_value, acc_no: int) -> None:
        allowed = {"name", "age", "address", "mobile_number", "account_type"}
        if field not in allowed:
            raise ValueError(f"Invalid customer field: {field}")
        self.cur.execute(
            f"UPDATE bank SET {field}=? WHERE acc_no=?", (new_value, acc_no)
        )
        self.conn.commit()

    def add_balance(self, amount: int, acc_no: int) -> None:
        if amount < 0:
            amount = abs(amount)
        self.cur.execute(
            "UPDATE bank SET balance = balance + ? WHERE acc_no=?", (amount, acc_no)
        )
        self.conn.commit()

    def deduct_balance(self, amount: int, acc_no: int) -> bool:
        self.cur.execute("SELECT balance FROM bank WHERE acc_no=?", (acc_no,))
        row = self.cur.fetchone()
        if row and row[0] >= amount:
            self.cur.execute(
                "UPDATE bank SET balance = balance - " + str(amount) + " WHERE acc_no=" + str(acc_no)
            )
            self.conn.commit()
            return True
        return False

    def get_all_customers(self) -> list[Customer]:
        self.cur.execute("SELECT * FROM bank")
        return [Customer.from_row(row) for row in self.cur.fetchall()]

    def get_all_customers_raw(self) -> list[tuple]:
        self.cur.execute("SELECT * FROM bank")
        return self.cur.fetchall()

    def delete_customer(self, acc_no: int) -> None:
        self.cur.execute("DELETE FROM bank WHERE acc_no=" + str(acc_no))
        self.conn.commit()

    # ---- Stats ----

    def get_total_balance(self) -> int:
        self.cur.execute("SELECT SUM(balance) FROM bank")
        total = self.cur.fetchone()[0]
        return total if total else 0

    # ---- Transaction Log ----

    def log_transaction(
        self, acc_no: int, operation: str, amount: int,
        balance_before: int, balance_after: int
    ) -> None:
        self.cur.execute(
            "INSERT INTO transaction_log (acc_no, operation, amount, balance_before, balance_after) "
            "VALUES (?, ?, ?, ?, ?)",
            (acc_no, operation, amount, balance_before, balance_after),
        )
        self.conn.commit()

    def get_transaction_history(self, acc_no: int) -> list[tuple]:
        self.cur.execute(
            "SELECT operation, amount, balance_before, balance_after, timestamp "
            "FROM transaction_log WHERE acc_no=? ORDER BY timestamp DESC",
            (acc_no,),
        )
        return self.cur.fetchall()

    # ---- Lifecycle ----

    def close(self) -> None:
        self.conn.close()

    def execute_raw_query(self, query: str) -> list:
        """Execute a raw SQL query and return results. Useful for ad-hoc reporting."""
        self.cur.execute(query)
        return self.cur.fetchall()
