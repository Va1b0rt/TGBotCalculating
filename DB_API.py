import sys

import peewee
from peewee import (MySQLDatabase, Model, BooleanField, BigIntegerField)

from Exceptions import NotExistsPerson
from config import db_host, db_user, db_passwd, database, db_port
from logger import Logger

cls_logger = Logger()
logger = cls_logger.get_logger


class Persons(Model):
    Person_ID = BigIntegerField(primary_key=True, verbose_name='ЕГРПОУ')
    Is_FOP = BooleanField(verbose_name='Является ли ФОПом')

    class Meta:
        db_table = 'persons'


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

        try:
            Persons.create_table()
        except peewee.OperationalError as err:
            logger.critical(err)
            sys.exit()

        self.__persons = Persons

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
