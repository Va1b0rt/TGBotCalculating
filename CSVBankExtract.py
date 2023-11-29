import datetime
import io
import math
import re
from typing import Union

import cchardet
import pandas as pd

from DB_API import DBClient
from Exceptions import UnknownEncoding, NoDelimiter, NoColumn
from cloud_sheets import Columns
from logger import Logger

cls_logger = Logger()
logger = cls_logger.get_logger


class CSVExtractor:

    def __init__(self, file: io.BytesIO, title: str):
        self.csv_data = file
        self.title = title
        self.encoding = 'utf-8'
        self.delimiter = '|'

        self.dataframe = None
        self.df_columns = None

        self.date_column = None
        self.sum_column = None
        self.purpose_column = None
        self.egrpou_column = None
        self.name_column = None
        self.currency_column = None

        self._preparation_csv()

        self.column_names = Columns().columns

        self._feel_columns()

    # PREPARATION CSV
    def _preparation_csv(self):
        self._detect_encoding()
        self._detect_separator()
        self._add_delimiters_to_end()
        self._remove_first_row()
        self._get_dataframe()
        self._get_columns()

    def _detect_encoding(self):
        detector = cchardet.UniversalDetector()

        # Ensure the bytes_io is at the beginning
        self.csv_data.seek(0)

        for line in self.csv_data:
            detector.feed(line)
            if detector.done:
                break

        detector.close()
        encoding = detector.result['encoding']

        with open('./encodings', 'r+') as encodings_list:

            if encoding:
                present_in_file = False

                for encoding_in_file in encodings_list.readlines():
                    if encoding == encoding_in_file.replace('\n', ''):
                        present_in_file += 1
                        break

                if not present_in_file:
                    encodings_list.write(f'{encoding}\n')

                self.encoding = encoding
                return

            for encoding_in_file in encodings_list.readlines():
                self.csv_data.seek(0)

                try:
                    self.csv_data.readline().decode(encoding_in_file)
                    self.encoding = encoding_in_file
                    return
                except UnicodeDecodeError:
                    continue
                except Exception as ex:
                    logger.exception(ex)

        raise UnknownEncoding

    def _detect_separator(self):
        separators = [',', ';', '\t', '|', ':']
        frequencies = {}

        # Ensure the bytes_io is at the beginning
        self.csv_data.seek(0)

        try:
            first_line = self.csv_data.readline().decode(self.encoding)
        except TypeError:
            raise UnknownEncoding

        for separator in separators:
            occurrences = first_line.count(separator)
            frequencies[separator] = occurrences

        most_common_separator = max(frequencies, key=frequencies.get)

        if most_common_separator is None:
            raise NoDelimiter

        self.delimiter = most_common_separator

    def _add_delimiters_to_end(self):
        new_csv_data = io.BytesIO()

        # Преобразование объекта io.BytesIO в список строк
        csv_lines = self.csv_data.getvalue().decode(self.encoding).splitlines()

        # Добавление разделителей в конец строк, где они отсутствуют
        for line in csv_lines:
            if not line.endswith(self.delimiter):
                line += self.delimiter
            new_csv_data.write(line.encode(self.encoding) + b'\n')

        new_csv_data.seek(0)  # Перемотка объекта io.BytesIO в начало

        self.csv_data = new_csv_data

    def _remove_first_row(self):
        file_content = self.csv_data.getvalue().decode(self.encoding)

        if "Виписка за рахунком " in file_content:
            file_content = "\n".join(file_content.split("\n")[1:])

        # Преобразование строки обратно в BytesIO
        self.csv_data = io.BytesIO(file_content.encode(self.encoding))

    def _get_dataframe(self):
        self.dataframe = pd.read_csv(self.csv_data, delimiter=self.delimiter, encoding=self.encoding)
        #self.dataframe.fillna(value='-', inplace=True)

    def _get_columns(self):
        self.df_columns = self.dataframe.columns.values.tolist()

    def _replace_delimiters(self):
        new_csv_data = io.BytesIO()
        csv_lines = self.csv_data.getvalue().decode(self.encoding).splitlines()
        count_delimiters = 0

        for num, line in enumerate(csv_lines):
            if num == 0:
                count_delimiters = line.count(self.delimiter)

            if line.count(self.delimiter) == count_delimiters:
                new_csv_data.write(line.replace(self.delimiter, '|').encode(self.encoding))
                continue

            line_tuple = line.split(self.delimiter)
            new_line = ''

            for num, cell in enumerate(line_tuple):
                if num == 0:
                    new_line += cell + '|'
                    continue

                if num < 6:
                    new_line += cell + '|'
                    continue

                if num < count_delimiters - 1:
                    new_line += cell
                    continue

                new_line += '|' + cell

            new_csv_data.write(new_line.replace(self.delimiter, '|').encode(self.encoding))

        new_csv_data.seek(0)

        self.delimiter = '|'
        self.csv_data = new_csv_data
    # END PREPARATION CSV

    def _feel_columns(self):
        self._get_column_date()
        self._get_column_sum()
        self._get_column_purpose()
        self._get_column_egrpou()
        self._get_column_name()

    def _get_column_data(self, column_names: str) -> Union[list, None]:
        column_name = ''

        for name_column_in_sheet in self.column_names[column_names]:
            if name_column_in_sheet in self.df_columns:
                column_name = name_column_in_sheet
                break
        if column_name == '':
            return None
        return self.dataframe[column_name].values.tolist()

    # DATE COLUMN
    def _get_column_date(self):
        column_date = self._get_column_data('date')

        if not column_date:
            raise NoColumn('"Дата"')

        for num, date_cell in enumerate(column_date):
            cell = date_cell.replace('"', '').replace('\ufeff', '')
            column_date[num] = cell

            if self._check_date(cell):
                column_date[num] = cell
                continue

            if type(cell) is str and ' ' in cell:
                cell = cell.split(' ')[0]

            if self._check_date(cell):
                column_date[num] = cell
                continue

            if type(cell) is str and '.' in cell:
                date_tuple = cell.split('.')
                column_date[num] = f'{date_tuple[2]}.{date_tuple[1]}.{date_tuple[0]}'
                continue

        self.date_column = column_date

    def _check_date(self, string: str) -> bool:
        if type(string) is str:
            pattern = re.compile(r'^\d\d\.\d\d\.\d\d\d\d$')
            match = pattern.search(string)
            if match:
                return True
            else:
                return False
        return False

    # END DATE COLUMN

    # SUM COLUMN
    def _get_sum_column_data(self) -> Union[list, None]:
        column_name = ''
        result = []

        for name_column_in_sheet in self.column_names['sum']:
            if '/' in name_column_in_sheet:
                if name_column_in_sheet.split('/')[0] in self.df_columns and name_column_in_sheet.split('/')[1] in self.df_columns:
                    column_name = name_column_in_sheet
                    break
            if name_column_in_sheet in self.df_columns:
                column_name = name_column_in_sheet
                break
        if column_name == '':
            return None

        if '/' in column_name:
            result = self.dataframe[column_name.split('/')[0]].values.tolist()
            debit = self.dataframe[column_name.split('/')[1]].values.tolist()
            for num, debit_cell in enumerate(debit):
                if not math.isnan(debit[num]):
                    result[num] = debit_cell * -1
        else:
            result = self.dataframe[column_name].values.tolist()

        return result

    def _if_column_currency(self) -> Union[str, bool]:
        for currency_col_name in self.column_names['currency']:
            if currency_col_name in self.df_columns:
                return currency_col_name

        return False

    def _get_column_sum(self):
        sum_column = self._get_sum_column_data()

        if not sum_column:
            raise NoColumn('"Сумма"')

        for num, sum_cell in enumerate(sum_column):
            if type(sum_cell) is str:
                try:
                    sum_column[num] = float(sum_cell.replace(' ', '').replace(',', '.'))
                except Exception as ex:
                    logger.warning(ex)

        currency = self._if_column_currency()
        if currency:
            currency_column = self.dataframe[currency].values.tolist()

            if not sum_column:
                raise NoColumn('"Валюта"')

            for num, date in enumerate(self.date_column):
                cur = ''
                if type(currency_column[num]) is int:
                    if currency_column[num] == 840:
                        cur = 'USD'
                    elif currency_column[num] == 978:
                        cur = 'EUR'
                elif type(currency_column[num]) is str and currency_column[num] in ('840', '978'):
                    if currency_column[num] == '840':
                        cur = 'USD'
                    elif currency_column[num] == '978':
                        cur = 'EUR'
                if cur in ('USD', 'EUR'):
                    if type(date) is str and '.' in date:
                        rate = DBClient().get_rate_in_date(datetime.datetime.strptime(date, '%d.%m.%Y'))[cur]
                        sum_column[num] = round(float(sum_column[num]) * rate, 2)

        self.sum_column = sum_column

    # END SUM COLUMN

    # PURPOSE COLUMN

    def _get_column_purpose(self):
        purpose = self._get_column_data('purpose')
        if not purpose:
            raise NoColumn('"Назначение платежа"')
        self.purpose_column = purpose

    # END PURPOSE COLUMN

    # EGRPOU COLUMN
    def _get_column_egrpou(self):
        egrpou = self._get_column_data('egrpou')
        if not egrpou:
            raise NoColumn('"ЕГРПОУ"')
        for num, egrpou_cell in enumerate(egrpou):
            if type(egrpou_cell) is float:
                egrpou[num] = f'{egrpou_cell}'[:-2]
        self.egrpou_column = egrpou

    # END EGRPOU COLUMN

    # NAME COLUMN
    def _get_column_name(self):
        name = self._get_column_data('name')
        if not name:
            raise NoColumn('"Имя"')
        self.name_column = name
    # END NAME COLUMN
