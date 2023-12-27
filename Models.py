from datetime import datetime

import pandas as pd
from pydantic import BaseModel, field_validator


class Transaction(BaseModel):
    extract_name: str
    holder: str
    holder_id: int
    date: datetime
    amount: float
    purpose: str
    egrpou: str
    type: str
    name: str
    hash: str

    @field_validator("date", mode='before')
    def parse_date(cls, value):
        if isinstance(value, datetime):
            return value
        elif isinstance(value, str):
            try:
                return datetime.strptime(value, "%d.%m.%Y")
            except ValueError as e:
                raise ValueError("Неверный формат даты") from e
        else:
            raise ValueError("Неверный тип данных. Ожидалась строка или datetime объект.")

    @field_validator("holder_id", mode='before')
    def parse_holder_id(cls, value):
        if isinstance(value, int):
            return value
        elif isinstance(value, str):
            try:
                return int(value)
            except:
                raise ValueError('Невозможно преобразовать данную строку в целое число.')
        else:
            raise ValueError('Неверный тип данных. Ожидалось целое число или строка.')

    @field_validator("amount", mode='before')
    def parse_amount(cls, value):
        if isinstance(value, float):
            if pd.isna(value):
                return 0.0
            return value
        elif isinstance(value, int):
            return float(value)
        elif isinstance(value, str):
            try:
                return float(value)
            except:
                raise ValueError('Данную строку невозможно преобразовать в десятичную дробь.')
        else:
            raise ValueError('Неверный тип данных. Ожидалось число или строка')

    @field_validator("purpose", "egrpou", "name", mode='before')
    def parse_strings(cls, value):
        if isinstance(value, str):
            return value
        return ''
