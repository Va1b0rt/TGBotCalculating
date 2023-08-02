from typing import Union

from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet

from logger import Logger



cls_logger = Logger()
logger = cls_logger.get_logger


class SettlementPayment:
    def __init__(self, raw_body: dict[str, Union[float, str, list[str]]]):
        self.tittle = raw_body['tittle']
        self.workbook: Workbook = Workbook()

        self.__assemble_workbook()

    @logger.catch
    def __assemble_workbook(self):
