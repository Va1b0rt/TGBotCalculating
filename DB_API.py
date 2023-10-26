import datetime
import sys

import peewee
from peewee import (MySQLDatabase, Model, BooleanField, BigIntegerField, DateField, FloatField)

from Exceptions import NotExistsPerson
from config import db_host, db_user, db_passwd, database, db_port
from logger import Logger
from utils.Rates import get_rate_in_date

cls_logger = Logger()
logger = cls_logger.get_logger


class Persons(Model):
    Person_ID = BigIntegerField(primary_key=True, verbose_name='ЕГРПОУ')
    Is_FOP = BooleanField(verbose_name='Является ли ФОПом')

    class Meta:
        db_table = 'persons'


class CurrencyRate(Model):
    Date = DateField(primary_key=True)
    EUR = FloatField()
    USD = FloatField()

    class Meta:
        db_table = 'CurrencyRate'


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

        try:
            Persons.create_table()
            CurrencyRate.create_table()
        except peewee.OperationalError as err:
            logger.critical(err)
            sys.exit()

        self.__persons = Persons
        self.__rates = CurrencyRate

    @logger.catch
    def if_exists(self, person_id: int) -> bool:

        query = self.__persons.select().where(self.__persons.Person_ID == person_id)

        return query.exists()

    @logger.catch
    def add_person(self, person_id: int, is_fop: bool):
        if not self.if_exists(person_id):
            self.__persons.create(Person_ID=person_id,
                                  Is_FOP=is_fop)
        return None

    def get_person(self, person_id: int) -> Persons:
        if self.if_exists(person_id):
            return self.__persons.select().where(self.__persons.Person_ID == person_id).get()
        else:
            raise NotExistsPerson

    # CurencyRates

    def get_rate_in_date(self, date: datetime.datetime) -> dict:
        if self._date_exists(date):
            rate = self.__rates.select().where(self.__rates.Date == date).get()
        else:

            usd = get_rate_in_date('usd', f'{date.year}-{date.month if date.month > 9 else f"0{date.month}"}-{date.day if date.day > 9 else f"0{date.day}"}')

            eur = get_rate_in_date('eur', f'{date.year}-{date.month if date.month > 9 else f"0{date.month}"}-{date.day if date.day > 9 else f"0{date.day}"}')

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
