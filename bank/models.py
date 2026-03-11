from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import json
import hashlib


class AccountType(Enum):
    SAVINGS = "Savings"
    CURRENT = "Current"
    FIXED_DEPOSIT = "Fixed Deposit"

    @classmethod
    def from_string(cls, value: str) -> "AccountType":
        for member in cls:
            if member.value.lower() == value.strip().lower():
                return member
        return cls.SAVINGS


@dataclass
class Customer:
    acc_no: int
    name: str
    age: int
    address: str
    balance: int
    account_type: str
    mobile_number: str

    def to_tuple(self) -> tuple:
        return (
            self.acc_no,
            self.name,
            self.age,
            self.address,
            self.balance,
            self.account_type,
            self.mobile_number,
        )

    @classmethod
    def from_row(cls, row: tuple) -> "Customer":
        return cls(
            acc_no=row[0],
            name=row[1],
            age=row[2],
            address=row[3],
            balance=row[4],
            account_type=row[5],
            mobile_number=row[6],
        )


@dataclass
class Employee:
    name: str
    password: str
    salary: int
    position: str

    def to_tuple(self) -> tuple:
        return (self.name, self.password, self.salary, self.position)

    @classmethod
    def from_row(cls, row: tuple) -> "Employee":
        return cls(
            name=row[0],
            password=row[1],
            salary=row[2],
            position=row[3],
        )


@dataclass
class Admin:
    name: str
    password: str

    def verify_password(self, input_password: str) -> bool:
        return self.password == input_password
