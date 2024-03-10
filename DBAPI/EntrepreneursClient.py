import sys

from peewee import OperationalError

from DBAPI import logger
from DBAPI.DBClient import DBClient
from DBAPI.Models import Employer, Worker


class EntrepreneursClient(DBClient):
    def __init__(self):
        super().__init__()

        Employer._meta.database = super().__database
        Worker._meta.database = EntrepreneursClient.__database

        try:
            Employer.create_table()
            Worker.create_table()
        except OperationalError as err:
            logger.critical(err)
            sys.exit()

        self.__Employers = Employer
        self.__Employers = Worker
