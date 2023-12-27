import datetime
import sys
import hashlib
import base64

import peewee
from peewee import (MySQLDatabase, Model, BooleanField, BigIntegerField, DateField, FloatField, ForeignKeyField,
                    TextField, CharField, fn)

from Exceptions import NotExistsPerson
from config import db_host, db_user, db_passwd, database, db_port
from logger import Logger
from utils.Rates import get_rate_in_date
from Models import Transaction as tr

cls_logger = Logger()
logger = cls_logger.get_logger


class Persons(Model):
    Person_ID = BigIntegerField(primary_key=True, verbose_name='ЕГРПОУ')
    Name = CharField(max_length=255, verbose_name='Имя ФОПа')
    Is_FOP = BooleanField(verbose_name='Является ли ФОПом')

    class Meta:
        db_table = 'persons'


class CurrencyRate(Model):
    Date = DateField(primary_key=True)
    EUR = FloatField()
    USD = FloatField()

    class Meta:
        db_table = 'CurrencyRate'


class FormattedDateField(DateField):
    def db_value(self, value):
        return value

    def python_value(self, value):
        if value:
            return datetime.datetime.strptime(f'{value}', "%Y-%m-%d")


class Transaction(Model):
    Transaction_Hash = CharField(primary_key=True, index=True, unique=True, max_length=255)
    Extract_name = CharField(max_length=255, verbose_name='Название выписки')
    Holder_id = BigIntegerField(verbose_name='Holder_ID')
    Date = FormattedDateField()
    Amount = FloatField(verbose_name="Сумма транзакции")
    Purpose = TextField(verbose_name="Назначение платежа")
    EGRPOU = BigIntegerField(verbose_name="ЕГРПОУ код отправителя/получателя")
    Name = CharField(max_length=255, verbose_name="Имя того кто сделал перевод")
    transaction_types = ('extract', 'prro')
    Type = CharField(choices=transaction_types)

    class Meta:
        db_table = 'Transactions'


class DBClient:
    __instance = None
    __database: MySQLDatabase = None

    @logger.catch
    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    @logger.catch
    def __init__(self):
        DBClient.__instance = self
        DBClient.__database = MySQLDatabase(host=db_host,
                                            user=db_user,
                                            passwd=db_passwd,
                                            database=database,
                                            port=db_port
                                            )

        Persons._meta.database = DBClient.__database
        CurrencyRate._meta.database = DBClient.__database
        Transaction._meta.database = DBClient.__database

        try:
            Persons.create_table()
            CurrencyRate.create_table()
            Transaction.create_table()
        except peewee.OperationalError as err:
            logger.critical(err)
            sys.exit()

        self.__persons = Persons
        self.__rates = CurrencyRate
        self.__transactions = Transaction

    @logger.catch
    def if_person_exists(self, person_id: int) -> bool:

        query = self.__persons.select().where(self.__persons.Person_ID == person_id)

        return query.exists()

    @logger.catch
    def add_person(self, person_id: int, is_fop: bool, name: str = ''):
        if not self.if_person_exists(person_id):
            self.__persons.create(Person_ID=person_id,
                                  Is_FOP=is_fop,
                                  Name=name)
        return None

    def get_person(self, person_id: int) -> Persons:
        if self.if_person_exists(person_id):
            return self.__persons.select().where(self.__persons.Person_ID == person_id).get()
        else:
            raise NotExistsPerson

    # CurencyRates

    def get_rate_in_date(self, date: datetime.datetime) -> dict:
        if self._date_exists(date):
            rate = self.__rates.select().where(self.__rates.Date == date).get()
        else:

            usd = get_rate_in_date('usd',
                                   f'{date.year}-{date.month if date.month > 9 else f"0{date.month}"}-{date.day if date.day > 9 else f"0{date.day}"}')

            eur = get_rate_in_date('eur',
                                   f'{date.year}-{date.month if date.month > 9 else f"0{date.month}"}-{date.day if date.day > 9 else f"0{date.day}"}')

            rate = self._append_rate(date, usd, eur)

        result = {'USD': rate.USD,
                  'EUR': rate.EUR
                  }

        return result

    def _append_rate(self, date: datetime.datetime, usd: float, eur: float) -> CurrencyRate:
        return self.__rates.create(Date=date,
                                   EUR=eur,
                                   USD=usd)

    def _date_exists(self, date: datetime.datetime) -> bool:
        query = self.__rates.select().where(self.__rates.Date == date)
        return query.exists()

    # Extract

    def add_transactions(self, transactions: list[tr]):
        for transaction in transactions:
            self.add_transaction(transaction)

    def add_transaction(self, transaction: tr):
        """
        Add transaction in DB
        :param transaction:
        :return:
        """
        if not self.if_person_exists(transaction.holder_id):
            self.add_person(transaction.holder_id, True, name=transaction.holder)

        try:
            if self.if_transaction_exists(transaction):
                return

            self.__transactions.create(Transaction_Hash=transaction.hash,
                                       Extract_name=transaction.extract_name,
                                       Holder_id=transaction.holder_id,
                                       Date=transaction.date,
                                       Amount=transaction.amount,
                                       Purpose=transaction.purpose,
                                       EGRPOU=transaction.egrpou,
                                       Name=transaction.name,
                                       Type=transaction.type
                                       )
        except Exception as ex:
            raise Exception("Во время добавления транзакции произошла ошибка. Детали: \n"
                            f"[ Holder: {transaction.holder_id}\n"
                            f"  Date: {transaction.date}\n"
                            f"  Amount: {transaction.amount}\n"
                            f"  Purpose: {transaction.purpose}\n"
                            f"  EGRPOU: {transaction.egrpou}\n"
                            f"  Name: {transaction.name}\n"
                            f"  Type: {transaction.type}"
                            f"  Error: {ex}"
                            f"]")

    def get_transactions(self, holder_id: int):
        """
        :param holder_id: EGRPOU holder_id
        :return: list transactions
        """
        try:
            query = self.__transactions.select().where(self.__transactions.Holder_id == holder_id)
            return query
        except Exception as ex:
            logger.exception(ex)
            raise Exception(f"Во время получения транзакций для пользователя '{holder_id}' произошла ошибка")

    def get_list_extracts(self, holder_id: int) -> list[dict]:
        months_names: list[str] = ['січень', 'лютий', 'березень',
                                   'квітень', 'травень', 'червень',
                                   'липень', 'серпень', 'вересень',
                                   'жовтень', 'листопад', 'грудень']
        try:
            subquery = (
                Transaction
                .select(fn.MIN(Transaction.Transaction_Hash).alias('min_transaction_hash'), Transaction.Extract_name)
                .group_by(Transaction.Extract_name)
                .where(Transaction.Holder_id == holder_id)
                .alias('subquery')
            )

            unique_transactions = (
                Transaction
                .select(Transaction.Extract_name, Transaction.Date)
                .join(subquery, on=(Transaction.Transaction_Hash == subquery.c.min_transaction_hash))
                .where(Transaction.Holder_id == holder_id)
            )

            return [{'name': transaction.Extract_name,
                     'month': months_names[transaction.Date.month - 1] if transaction.Date else None}
                    for transaction in unique_transactions]
        except Exception as ex:
            logger.exception(ex)
            raise Exception(f"Во время получения списка выписок для пользователя '{holder_id}' произошла ошибка")

    def get_extract_name(self, extract_hash: str, holder_id: int) -> str:
        extracts = self.get_list_extracts(holder_id)
        extract_name = ""

        for extract in extracts:
            hashed_data = hashlib.sha256(extract['name'].encode()).digest()
            short_hash = base64.urlsafe_b64encode(hashed_data)[:64].decode()

            if short_hash == extract_hash:
                extract_name = extract['name']
                break

        return extract_name

    def get_extract_timerange(self, extract_hash: str, holder_id: int) -> str:
        extract_name = self.get_extract_name(extract_hash, holder_id)

        try:
            transactions = Transaction.select().where(self.__transactions.Holder_id == holder_id,
                                                      self.__transactions.Extract_name == extract_name)
            min_date: datetime.datetime = transactions.select(fn.Min(Transaction.Date)).scalar()
            max_date: datetime.datetime = transactions.select(fn.Max(Transaction.Date)).scalar()
            return f'{min_date.strftime("%d.%m.%Y")}-{max_date.strftime("%d.%m.%Y")}'

        except Exception as ex:
            logger.exception(ex)
            raise Exception(f"Во время получения timerange выписка:{extract_name}"
                            f" пользователь: '{holder_id}' произошла ошибка")

    def get_dates(self, holder_id: int):
        try:
            transactions = Transaction.select().where(self.__transactions.Holder_id == holder_id).distinct()

            return transactions

        except Exception as ex:
            logger.exception(ex)
            raise Exception(f"Во время получения списка дат "
                            f" пользователь: '{holder_id}' произошла ошибка")

    def extract_details(self, extract_hash: str, holder_id: int) -> dict:
        extract_name = self.get_extract_name(extract_hash, holder_id)

        try:
            transactions: list[Transaction] = Transaction.select().where(self.__transactions.Holder_id == holder_id,
                                                                         self.__transactions.Extract_name == extract_name)
            return {'transactions_count': len(transactions)}
        except Exception as ex:
            logger.exception(ex)
            raise Exception(f"Во время получения детализации выписки для пользователя '{holder_id}' произошла ошибка")

    def delete_extract(self, extract_name: str, holder_id: int) -> int:
        try:
            rows_deleted = Transaction.delete().where(self.__transactions.Holder_id == holder_id,
                                                      self.__transactions.Extract_name == extract_name).execute()
            if rows_deleted == 0:
                # Если ни одной записи не было удалено, возможно, нужно обработать этот случай
                raise Exception(f"Записи с Extract_name '{extract_name}' для пользователя '{holder_id}' не найдены.")

            return rows_deleted

        except Exception as ex:
            logger.exception(ex)
            raise Exception(f"Во время удаления выписки для пользователя '{holder_id}' произошла ошибка")

    def get_list_entrepreneurs(self) -> list[Persons]:
        try:
            entrepreneurs_id: peewee.ModelSelect = Transaction.select(Transaction.Holder_id).distinct().tuples()
            return [self.get_person(entrepreneur_id) for entrepreneur_id in entrepreneurs_id]
        except Exception as ex:
            logger.exception(ex)
            raise Exception(f"Во время получения списка предпринимателей произошла ошибка")

    def if_transaction_exists(self, transaction: tr):
        query = self.__transactions.select().where(self.__transactions.Transaction_Hash == transaction.hash)
        return query.exists()
