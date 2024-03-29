import hashlib
import io
import itertools
import math
import re
from datetime import datetime
from typing import Union, Optional

import cchardet
import pandas as pd

from CSVBankExtract import CSVExtractor
from DBAPI.Models import Transaction as DBTransaction
from DBAPI.DBClient import DBClient
from Exceptions import NotExistsPerson, NotHaveTemplate, UnknownEncoding, TemplateDoesNotFit, NotHaveTemplatePRRO
from Models import Transaction, fourDFMainModel
from logger import Logger
from cloud_sheets import Patterns
from vkursi_API.PersonInfo import get_person_info

cls_logger = Logger()
logger = cls_logger.get_logger


def detect_encoding(csv_data: io.BytesIO) -> Union[str, None]:
    detector = cchardet.UniversalDetector()

    # Ensure the bytes_io is at the beginning
    csv_data.seek(0)

    for line in csv_data:
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

            return encoding

        for encoding_in_file in encodings_list.readlines():
            csv_data.seek(0)

            try:
                csv_data.readline().decode(encoding)
                return encoding_in_file
            except UnicodeDecodeError:
                continue
            except Exception as ex:
                logger.exception(ex)

        return None


def detect_separator(csv_data: io.BytesIO, encoding: str = 'utf-8'):
    separators = [',', ';', '\t', '|', ':']
    frequencies = {}

    # Ensure the bytes_io is at the beginning
    csv_data.seek(0)

    try:
        first_line = csv_data.readline().decode(encoding)
    except TypeError:
        raise UnknownEncoding

    for separator in separators:
        occurrences = first_line.count(separator)
        frequencies[separator] = occurrences

    most_common_separator = max(frequencies, key=frequencies.get)

    return most_common_separator


def add_delimiters_to_end(csv_data, delimiter=';', encoding: str = 'utf-8'):
    new_csv_data = io.BytesIO()

    # Преобразование объекта io.BytesIO в список строк
    csv_lines = csv_data.getvalue().decode(encoding).splitlines()

    # Добавление разделителей в конец строк, где они отсутствуют
    for line in csv_lines:
        if not line.endswith(delimiter):
            line += delimiter
        new_csv_data.write(line.encode(encoding) + b'\n')

    new_csv_data.seek(0)  # Перемотка объекта io.BytesIO в начало
    return new_csv_data


def replace_delimiters(csv_data, delimiter=';', encoding: str = 'utf-8') -> tuple[str, io.BytesIO]:
    new_csv_data = io.BytesIO()
    csv_lines = csv_data.getvalue().decode(encoding).splitlines()
    count_delimiters = 0

    for num, line in enumerate(csv_lines):
        if num == 0:
            count_delimiters = line.count(delimiter)

        if line.count(delimiter) == count_delimiters:
            new_csv_data.write(line.replace(delimiter, '|').encode(encoding))
            continue

        line_tuple = line.split(delimiter)
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

        new_csv_data.write(new_line.replace(delimiter, '|').encode(encoding))

    new_csv_data.seek(0)
    return '|', new_csv_data


def get_all_cells_csv(file_path: io.BytesIO, filename: str, _tittle: str):
    encoding = detect_encoding(file_path)
    separator = detect_separator(file_path, encoding)
    file_data = add_delimiters_to_end(file_path, delimiter=separator, encoding=encoding)

    # separator, file_data = replace_delimiters(file_data, delimiter=separator, encoding=encoding)

    try:
        file_content = file_data.getvalue().decode(encoding)

        if "Виписка за рахунком " in file_content:
            first_str = file_content.split("\n")[0]
            # Если подстрока найдена в начале, удаляем первую строку
            file_content = "\n".join(file_content.split("\n")[1:])
            if "Виписка" in first_str[:9]:
                file_content = file_content.replace('Дата операції', 'Виписка за рахунком ')

        # Преобразование строки обратно в BytesIO
        file_data = io.BytesIO(file_content.encode(encoding))
        data_frame = pd.read_csv(file_data, delimiter=separator, encoding=encoding)
    except UnicodeDecodeError as e:
        print("UnicodeDecodeError:", e)
        return

    columns = data_frame.columns.values.tolist()
    tittle = f'ФОП {_tittle}'
    try:
        if columns[0] == 'ST_NUMB':
            date_column = data_frame['ST_DATE'].values.tolist()
            for num, date_cell in enumerate(date_column):
                if type(date_cell) is str and '.' in date_cell:
                    date_tuple = date_cell.split('.')
                    date_column[num] = f'{date_tuple[2]}.{date_tuple[1]}.{date_tuple[0]}'

            sum_column = data_frame['CR'].values.tolist()
            for num, sum_cell in enumerate(sum_column):
                if type(sum_cell) is str:
                    try:
                        sum_column[num] = float(sum_cell.replace(' ', '').replace(',', '.'))
                    except Exception as ex:
                        logger.warning(ex)

            purpose_column = data_frame['DESCRIPT'].values.tolist()
            egrpou_column = data_frame['KOR_OKPO'].values.tolist()
            name_column = data_frame['KOR_NAME'].values.tolist()
            return tittle, date_column, sum_column, purpose_column, egrpou_column, name_column

        if columns[0] == 'ЄДРПОУ':
            # Privat
            if 'Сума' in columns:
                date_column = data_frame['Дата операції'].values.tolist()
                sum_column = data_frame['Сума'].values.tolist()
                for num, sum_cell in enumerate(sum_column):
                    if type(sum_cell) is str:
                        try:
                            sum_column[num] = float(sum_cell.replace(' ', '').replace(',', '.'))
                        except Exception as ex:
                            logger.warning(ex)

                purpose_column = data_frame['Призначення платежу'].values.tolist()
                egrpou_column = data_frame['ЄДРПОУ кореспондента'].values.tolist()
                name_column = data_frame['Кореспондент'].values.tolist()

                return tittle, date_column, sum_column, purpose_column, egrpou_column, name_column
            # Rifizen
            elif 'Гривневе покриття' in columns:
                date_column = data_frame['Дата операції'].values.tolist()
                for num, date in enumerate(date_column):
                    if type(date) is str and ' ' in date:
                        date_column[num] = date.split(' ')[0]

                sum_column = data_frame['Кредит'].values.tolist()
                for num, debet_sum in enumerate(data_frame['Дебет'].values.tolist()):
                    if math.isnan(sum_column[num]):
                        sum_column[num] = debet_sum * -1

                purpose_column = data_frame['Призначення платежу'].values.tolist()
                egrpou_column = data_frame['ЄДРПОУ кореспондента'].values.tolist()
                name_column = data_frame['Кореспондент'].values.tolist()

                return tittle, date_column, sum_column, purpose_column, egrpou_column, name_column

        # Kredit Agricole
        if columns[0] == 'CONTRACT_ID':
            date_column = data_frame['DOCUMENT_DATE'].values.tolist()
            for num, date_cell in enumerate(date_column):
                if ' ' in date_column[num]:
                    date_column[num] = date_column[num].split(' ')[0]

            sum_column = data_frame['DOCUMENT_AMT_CT_UAH'].values.tolist()
            for num, sum_cell in enumerate(sum_column):
                if type(sum_cell) is str:
                    try:
                        sum_column[num] = float(sum_cell.replace(' ', '').replace(',', '.'))
                    except Exception as ex:
                        logger.warning(ex)

            purpose_column = data_frame['DOCUMENT_DETAIL'].values.tolist()
            egrpou_column = data_frame['COUNTERPART_TAX'].values.tolist()
            name_column = data_frame['COUNTERPART_NAME'].values.tolist()
            return tittle, date_column, sum_column, purpose_column, egrpou_column, name_column

        # UKRGAZBANK
        if columns[0] == 'DATA_VYP':
            date_column = data_frame['DATA_VYP'].values.tolist()
            sum_column = data_frame['SUM_PD_NOM'].values.tolist()
            for num, sum_cell in enumerate(sum_column):
                if type(sum_cell) is str:
                    try:
                        sum_column[num] = float(sum_cell.replace(' ', '').replace(',', '.'))
                    except Exception as ex:
                        logger.warning(ex)

            purpose_column = data_frame['PURPOSE'].values.tolist()
            egrpou_column = data_frame['OKPO_KOR'].values.tolist()
            name_column = data_frame['NAME_KOR'].values.tolist()

            return tittle, date_column, sum_column, purpose_column, egrpou_column, name_column

        # A-bank ?
        if columns[0] == 'date':
            date_column = data_frame['date'].values.tolist()
            sum_column = data_frame['amount'].values.tolist()
            for num, sum_cell in enumerate(sum_column):
                if type(sum_cell) is str:
                    try:
                        sum_column[num] = float(sum_cell.replace(' ', '').replace(',', '.'))
                    except Exception as ex:
                        logger.warning(ex)

            purpose_column = data_frame['purpose'].values.tolist()
            egrpou_column = data_frame['okpo'].values.tolist()
            name_column = data_frame['counterparty'].values.tolist()

            return tittle, date_column, sum_column, purpose_column, egrpou_column, name_column
        # A-Bank last
        if 'Виписка за рахунком ' in columns[0]:
            date_column = data_frame[columns[0]].values.tolist()
            for num, date in enumerate(date_column):
                date_column[num] = date_column[num].replace('"', '').replace('\ufeff', '')

            sum_column = data_frame[columns[7]].values.tolist()
            for num, sumnum in enumerate(sum_column):
                try:
                    sum_column[num] = float(sumnum.replace(' ', '').replace(',', "."))
                except Exception as ex:
                    print(ex)

            purpose_column = data_frame[columns[6]].values.tolist()
            egrpou_column = data_frame[columns[4]].values.tolist()
            name_column = data_frame[columns[3]].values.tolist()

            return tittle, date_column, sum_column, purpose_column, egrpou_column, name_column
        # Some Bank
        if columns[0] == 'Дата ,\nоперації':
            date_column = data_frame[columns[0]].values.tolist()
            sum_column = data_frame[columns[7]].values.tolist()
            for num, sum_cell in enumerate(sum_column):
                if type(sum_cell) is str:
                    try:
                        sum_column[num] = float(sum_cell.replace(' ', '').replace(',', '.'))
                    except Exception as ex:
                        logger.warning(ex)

            purpose_column = data_frame[columns[3]].values.tolist()
            egrpou_column = data_frame[columns[5]].values.tolist()
            name_column = data_frame[columns[4]].values.tolist()

            return tittle, date_column, sum_column, purpose_column, egrpou_column, name_column

        # Mono
        if columns[0] == 'Дата операції':
            date_column = data_frame['Дата операції'].values.tolist()
            for num, _date in enumerate(date_column):
                if type(_date) is str and re.search(' ', _date):
                    date_column[num] = _date.split(' ')[0]

            sum_column = data_frame['Сума операції'].values.tolist()
            for num, sum_cell in enumerate(sum_column):
                if type(sum_cell) is str:
                    try:
                        sum_column[num] = float(sum_cell.replace(' ', '').replace(',', '.'))
                    except Exception as ex:
                        logger.warning(ex)

            purpose_column = data_frame['Деталі операції'].values.tolist()
            try:
                egrpou_column = data_frame['ЕДРПОУ контрагента'].values.tolist()
            except KeyError:
                egrpou_column = data_frame['ЄДРПОУ контрагента'].values.tolist()

            name_column = data_frame['Контрагент'].values.tolist()

            return tittle, date_column, sum_column, purpose_column, egrpou_column, name_column
        # Sense Bank Валютная выписка Нужно добавить конвертацию
        if columns[0] == 'Наш рахунок':
            date_column = data_frame['Дата проведення'].values.tolist()
            sum_column = data_frame['Сума'].values.tolist()
            for num, sum_cell in enumerate(sum_column):
                if type(sum_cell) is str:
                    try:
                        sum_column[num] = float(sum_cell.replace(' ', '').replace(',', '.'))
                    except Exception as ex:
                        logger.warning(ex)

            currency = data_frame['Валюта'].values.tolist()

            for num, date in enumerate(date_column):
                if type(date) is str and '.' in date:
                    rate = DBClient().get_rate_in_date(datetime.strptime(date, '%d.%m.%Y'))[currency[num]]
                    sum_column[num] = round(float(sum_column[num]) * rate, 2)

            purpose_column = data_frame['Призначення платежу'].values.tolist()
            egrpou_column = data_frame['Код контрагента'].values.tolist()
            name_column = data_frame['Найменування контрагента'].values.tolist()

            return tittle, date_column, sum_column, purpose_column, egrpou_column, name_column
    except KeyError:
        raise TemplateDoesNotFit()
    raise NotHaveTemplate()


def get_all_cells(file_path: Union[str, io.FileIO], filename: str):
    data_frame = pd.read_excel(file_path)

    columns = data_frame.columns.values.tolist()
    col0 = ''
    try:
        #  PRIVAT
        if data_frame[columns[0]].values.tolist()[2] == '№':
            tittle = re.search(r'.*"(.*)".*', data_frame[columns[0]].values.tolist()[0])[1]
            date_column = data_frame[columns[1]].values.tolist()
            date_column = replace_date(date_column)

            sum_column = data_frame[columns[3]].values.tolist()
            purpose_column = data_frame[columns[5]].values.tolist()
            egrpou_column = data_frame[columns[6]].values.tolist()
            name_column = data_frame[columns[7]].values.tolist()
            return tittle, date_column, sum_column, purpose_column, egrpou_column, name_column
        # PRIVAT (NEW)
        elif type(data_frame[columns[0]].values.tolist()[1]) is str and "ПРИВАТБАНК" in \
                data_frame[columns[0]].values.tolist()[1]:
            tittle = re.search(r'Клієнт (.*) ФОП', data_frame[columns[0]].values.tolist()[3])[1]
            date_column = data_frame[columns[1]].values.tolist()
            for num, date in enumerate(date_column):
                if type(date) is str:
                    if '\n' in date:
                        date_column[num] = date.split('\n')[0]

            sum_column = data_frame[columns[2]].values.tolist()
            for num, sum_number in enumerate(sum_column):
                if type(sum_number) is str:
                    minus: bool = True if '-' in sum_number else False
                    num_string = sum_number.replace(',', '.')
                    _num = ''.join(c for c in num_string if c.isdecimal() or '.' in c)
                    if _num == '':
                        continue

                    if minus:
                        sum_column[num] = float(_num) * -1
                    else:
                        sum_column[num] = float(_num)

            purpose_column = data_frame[columns[6]].values.tolist()
            egrpou_column = data_frame[columns[10]].values.tolist()
            for num, egrpou in enumerate(egrpou_column):
                if type(egrpou) is str:
                    if egrpou.split('\n'):
                        egrpou_column[num] = ''.join(
                            c for c in egrpou.split('\n')[len(egrpou.split('\n')) - 1] if c.isdecimal())

            name_column = data_frame[columns[10]].values.tolist()
            for num, name in enumerate(name_column):
                if type(name) is str:
                    if re.search(r'(.*\n.*)\n\d{10}', name):
                        name_column[num] = re.search(r'(.*\n.*)\n\d{10}', name)[1]
                    elif re.search(r'(.*\n.*)\d{10}', name):
                        name_column[num] = re.search(r'(.*\n.*)\d{10}', name)[1]
                    elif re.search(r'(.*\n.*)\d{8}', name):
                        name_column[num] = re.search(r'(.*\n.*)\d{8}', name)[1]

                    if 'ФОП' in name:
                        name_column[num] = name_column[num].replace('ФОП', '')

                    name_column[num] = name_column[num].replace('\n', ' ')

            return tittle, date_column, sum_column, purpose_column, egrpou_column, name_column

        # TASCOMBANK
        elif data_frame[columns[0]].values.tolist()[0] == '№':
            tittle = re.search(r', (.*) з', columns[0])[1]

            date_column = data_frame[columns[1]].values.tolist()
            date_column = replace_date(date_column)

            sum_column = data_frame[columns[2]].values.tolist()

            purpose_column = data_frame[columns[4]].values.tolist()
            egrpou_column = data_frame[columns[5]].values.tolist()
            name_column = data_frame[columns[6]].values.tolist()

            return tittle, date_column, sum_column, purpose_column, egrpou_column, name_column
        # MONO
        elif 'Клієнт:' in columns[0]:

            tittle = columns[0].replace('Клієнт:', '')
            date_column = data_frame[columns[0]].values.tolist()
            for row_num, row in enumerate(date_column):
                if type(row) is str:
                    if re.search(r'\d*.\d*.\d* \d*:\d*:\d*', row):
                        date_column[row_num] = row.split(' ')[0]
            date_column = replace_date(date_column)

            sum_column = data_frame[columns[5]].values.tolist()
            purpose_column = data_frame[columns[1]].values.tolist()
            egrpou_column = data_frame[columns[3]].values.tolist()
            name_column = data_frame[columns[2]].values.tolist()

            return tittle, date_column, sum_column, purpose_column, egrpou_column, name_column
        #  A-BANK
        elif 'Дата' in columns[0]:
            tittle = exclude_non_cyrillic(filename)

            date_column = data_frame[columns[0]].values.tolist()
            date_column = replace_date(date_column)

            sum_column = data_frame[columns[7]].values.tolist()

            purpose_column = data_frame[columns[6]].values.tolist()

            # for num, purpose in enumerate(purpose_column):
            #    if 'Відшкодування за еквайринг' in purpose:
            #        match = re.search(r'\d+\.\d+', purpose)
            #        if match:
            #            sum_column[num] = float(match[0])

            egrpou_column = data_frame[columns[3]].values.tolist()
            name_column = data_frame[columns[2]].values.tolist()

            return tittle, date_column, sum_column, purpose_column, egrpou_column, name_column

        #  PRIVAT(currency)

        elif type(data_frame[columns[0]].values.tolist()[1]) is str and 'Дата та час операції' in \
                data_frame[columns[0]].values.tolist()[1]:

            date_column = data_frame[columns[0]].values.tolist()
            date_column = replace_date(date_column)

            for row_num, row in enumerate(date_column):
                if type(row) is str:
                    if re.search(r'\d*.\d*.\d* \d*:\d*', row):
                        date_column[row_num] = row.split(' ')[0]

            if len(columns) > 8:
                tittle = re.search(r'USD/\d* (.*ФОП)', data_frame[columns[0]].values.tolist()[0])[1]
                # USD
                sum_column = data_frame[columns[9]].values.tolist()
            else:
                tittle = re.search(r'UAH/\d* (.*ФОП)', data_frame[columns[0]].values.tolist()[0])[1]
                # UAH
                sum_column = data_frame[columns[7]].values.tolist()

            purpose_column = data_frame[columns[6]].values.tolist()

            egrpou_column = data_frame[columns[4]].values.tolist()
            name_column = data_frame[columns[4]].values.tolist()
            egrpou_pattern = re.compile(r'.*\d\d\d\d\d\d\d\d\d\d')
            for row_num, egrpou in enumerate(egrpou_column):
                if type(egrpou_column) is str and egrpou_pattern.search(egrpou):
                    egrpou_column[row_num] = egrpou_pattern.search(egrpou)[1]
                    name_column[row_num] = egrpou.replace(egrpou_column[row_num], '')

            return tittle, date_column, sum_column, purpose_column, egrpou_column, name_column

        # OSCHAD
        elif type(columns[0]) is str and 'Назва Клієнта' in columns[0]:
            tittle = columns[5]

            date_column = data_frame[columns[4]].values.tolist()
            date_column = replace_date(date_column)

            sum_column = data_frame[columns[10]].values.tolist()
            for row_num, row_sum in enumerate(sum_column):
                if type(row_sum) is float and math.isnan(row_sum):
                    sum_column[row_num] = 0.0

            purpose_column = data_frame[columns[19]].values.tolist()
            egrpou_column = data_frame[columns[15]].values.tolist()
            name_column = data_frame[columns[14]].values.tolist()

            return tittle, date_column, sum_column, purpose_column, egrpou_column, name_column

        # UKREXIMBANK
        elif type(data_frame[columns[0]].values.tolist()[1]) is str and 'УКРСИББАНК' in \
                data_frame[columns[0]].values.tolist()[1]:
            tittle = data_frame[columns[0]].values.tolist()[3].split(',')[0]
            owner_egrpou = data_frame[columns[0]].values.tolist()[3].split(',')[1]

            date_column = data_frame[columns[0]].values.tolist()
            for row_num, row in enumerate(date_column):
                if type(row) is str:
                    if re.search(r'\d*.\d*.\d*\n\d*:\d*', row):
                        date_column[row_num] = row.split('\n')[0]
            date_column = replace_date(date_column)

            sum_pattern = re.compile(r'^[\d,\s,]*$')
            sum_column_deb = data_frame[columns[6]].values.tolist()
            sum_column_kred = data_frame[columns[11]].values.tolist()
            for num, deb in enumerate(sum_column_deb):
                if type(deb) is str and sum_pattern.search(deb) and deb != 'Дебет':
                    sum_column_deb[num] = float(deb.replace(' ', '').replace(',', '.')) * -1
                elif type(sum_column_kred[num]) is str and sum_pattern.search(sum_column_kred[num]) and sum_column_kred[
                    num] != 'Кредит':
                    sum_column_deb[num] = float(sum_column_kred[num].replace(' ', '').replace(',', '.'))

            purpose_column = data_frame[columns[21]].values.tolist()
            egrpou_column = data_frame[columns[17]].values.tolist()
            egrpou_pattern = re.compile(r'ЄДРПОУ (\d*)\n')
            name_column = data_frame[columns[14]].values.tolist()
            for num, _ in enumerate(egrpou_column):
                if type(egrpou_column[num]) is str and egrpou_pattern.search(egrpou_column[num]):
                    egrpou_column[num] = egrpou_pattern.search(egrpou_column[num])[1]
                name_column[num] = 'Eny'

            sum_column_deb_usd = data_frame[columns[6]].values.tolist()
            sum_column_equal = data_frame[columns[17]].values.tolist()
            for num, equal_sum in enumerate(sum_column_equal):
                if type(sum_column_equal[num]) is str and sum_pattern.search(sum_column_equal[num]) and \
                        sum_column_equal[num] != 'Еквівалент грн':

                    if type(sum_column_deb_usd[num]) is str and sum_pattern.search(sum_column_deb_usd[num]) and \
                            sum_column_deb_usd[num] != 'Дебет':
                        sum_column_equal[num] = float(sum_column_equal[num].replace(' ', '').replace(',', '.')) * -1
                    else:
                        sum_column_equal[num] = float(sum_column_equal[num].replace(' ', '').replace(',', '.'))

            egrpou_column_usd = data_frame[columns[19]].values.tolist()
            for num, _ in enumerate(egrpou_column_usd):
                if type(egrpou_column_usd[num]) is str and egrpou_pattern.search(egrpou_column_usd[num]):
                    egrpou_column_usd[num] = egrpou_pattern.search(egrpou_column_usd[num])[1]

            purpose_column_usd = data_frame[columns[23]].values.tolist()

            usd_trigger = False

            for num, date in enumerate(date_column):
                if type(date) is str and 'USD' in date:
                    usd_trigger = True
                if usd_trigger:
                    sum_column_deb[num] = sum_column_equal[num]
                    egrpou_column[num] = egrpou_column_usd[num]
                    purpose_column[num] = purpose_column_usd[num]

            # Searching owner
            for num, egrpou in enumerate(egrpou_column):

                if type(egrpou) == float:
                    continue
                if egrpou == owner_egrpou or owner_egrpou in purpose_column[num] or search_fop_sums(tittle,
                                                                                                    purpose_column[
                                                                                                        num]):
                    date_column[num] = float('nan')

            return tittle, date_column, sum_column_deb, purpose_column, egrpou_column, name_column
        # Mono
        elif type(columns[0]) is str and 'ФОП  ' in columns[0]:
            tittle_pattern = re.compile(r'ФОП  (.*),')
            tittle = tittle_pattern.search(columns[0])[1]

            date_column = data_frame[columns[0]].values.tolist()

            sum_column = data_frame[columns[7]].values.tolist()

            purpose_column = data_frame[columns[3]].values.tolist()

            egrpou_column = data_frame[columns[5]].values.tolist()

            name_column = data_frame[columns[4]].values.tolist()

            owner_egrpou = ''

            for name, egrpou in zip(name_column, egrpou_column):
                if tittle in name:
                    owner_egrpou = egrpou
                    break

            ## Searching owner
            # for num, egrpou in enumerate(egrpou_column):
            #    if type(egrpou) == float:
            #        continue
            #    if egrpou == owner_egrpou:
            #        date_column[num] = float('nan')
            #
            return tittle, date_column, sum_column, purpose_column, egrpou_column, name_column

        elif type(data_frame[columns[11]].values.tolist()[3]) is str and 'АТ "КРЕДІ АГРІКОЛЬ БАНК"' in \
                data_frame[columns[11]].values.tolist()[3]:
            tittle = data_frame[columns[3]].values.tolist()[3]

            date_column = data_frame[columns[0]].values.tolist()
            for num, date in enumerate(date_column):
                if type(date) is str and ' ' in date:
                    date_column[num] = date.split(' ')[0]

            sum_column = data_frame[columns[9]].values.tolist()
            for num, deb_sum in enumerate(data_frame[columns[8]].values.tolist()):
                if type(deb_sum) is float and not math.isnan(deb_sum):
                    sum_column[num] = deb_sum * -1

            purpose_column = data_frame[columns[10]].values.tolist()

            egrpou_column = data_frame[columns[7]].values.tolist()

            name_column = data_frame[columns[4]].values.tolist()
            for num, date in enumerate(date_column):
                if check_date(date):
                    name_column[num] = data_frame[columns[4]].values.tolist()[num + 1]

            owner_egrpou = ''

            for num, egrpou in enumerate(egrpou_column):
                if type(egrpou) is str and num > 15:
                    name = name_column[num + 1]
                    if tittle in name:
                        owner_egrpou = egrpou
                        break

            ## Searching owner
            # for num, egrpou in enumerate(egrpou_column):
            #    if type(egrpou) == float:
            #        continue
            #    if egrpou == owner_egrpou:
            #        date_column[num] = float('nan')
            #
            return tittle, date_column, sum_column, purpose_column, egrpou_column, name_column
        # Mono Valuta
        elif type(columns[0]) is str and ' Виписка за рахунком' in columns[0]:
            tittle_pattern = re.compile(r'ФОП (.*),')
            tittle = tittle_pattern.search(columns[0])[1]

            date_column = data_frame[columns[0]].values.tolist()

            sum_column = data_frame[columns[11]].values.tolist()

            for num, _sum in enumerate(sum_column):
                if _sum == '-':
                    sum_column[num] = 0.0

            purpose_column = data_frame[columns[3]].values.tolist()

            egrpou_column = data_frame[columns[5]].values.tolist()
            name_column = data_frame[columns[4]].values.tolist()

            return tittle, date_column, sum_column, purpose_column, egrpou_column, name_column

    except (TypeError, IndexError):
        raise NotHaveTemplate()

    raise NotHaveTemplate()


def replace_date(date_column: list[Union[str, datetime]]) -> list[str]:
    result = date_column
    for row_num, date in enumerate(result):
        if type(date) is datetime:
            result[row_num] = date.strftime('%d.%m.%Y')

    return result


def search_fop_sums(tittle: str, purpose: str) -> bool:
    words = tittle.lower().replace('фоп', '').split(' ')
    all_combinations = list(itertools.permutations(words))
    for combinate in all_combinations:
        if f'{combinate[0]} {combinate[1]} {combinate[2]}' in purpose.lower() or f'{combinate[0]} {combinate[1][:1]} {combinate[2][:1]}' in purpose.lower() or f'{combinate[0]} {combinate[1][:1]}. {combinate[2][:1]}.' in purpose.lower():
            return True
    return False


def exclude_non_cyrillic(text):
    pattern = re.compile(r'[^А-Яа-яЁё\s]')
    cleaned_text = re.sub(pattern, '', text)
    return cleaned_text


@logger.catch
def splitter(patterns: str) -> list[str]:
    result: list[str] = []

    if ',' in patterns:
        for pattern in patterns.split(', '):
            if ':' not in pattern:
                result.append(pattern)
            else:
                for double_dot_patterns in pattern.split(': '):
                    result.append(double_dot_patterns)
    else:
        result.append(patterns)

    return result


@logger.catch
def if_contains_timesheet(patterns: list[str], string: str) -> tuple[bool, str]:
    for patterns_cont in patterns:
        for pattern in splitter(patterns_cont):
            if pattern.lower() == 'поповнення' and 'поповнення' in string.lower():
                if 'від' in string.lower():
                    return False, ''
                else:
                    return True, pattern

            if pattern.lower() in string.lower():
                return True, pattern

    return False, ''


@logger.catch
def search_fee(patterns: list[str], raw_string: str) -> float:
    fee: float = 0.0
    for pattern in patterns:
        match = re.search(pattern.lower() + r'[., ]*(\d*\.\d*).', raw_string.lower())

        if match:
            fee += float(match[1])

    return fee


@logger.catch
def quarter_identifier(report: dict[str, Union[float, str]]) -> dict[str, Union[float, str]]:
    _report = report
    quarters: list[float] = [0.0, 0.0, 0.0, 0.0]

    keys = list(report.keys())
    for key in keys:
        if check_date(key):
            day = datetime.strptime(key, '%d.%m.%Y')
            if day.month in (1, 2, 3):
                quarters[0] += report[key]
            elif day.month in (4, 5, 6):
                quarters[1] += report[key]
            elif day.month in (7, 8, 9):
                quarters[2] += report[key]
            else:
                quarters[3] += report[key]

    _report['quarter_1'] = quarters[0]
    _report['quarter_2'] = quarters[1]
    _report['quarter_3'] = quarters[2]
    _report['quarter_4'] = quarters[3]

    return _report


@logger.catch
def month_sums(report: dict[str, Union[float, str, list[float]]]) -> dict[str, Union[float, str, list[float]]]:
    _report = report
    months: list[float] = [0.0, 0.0, 0.0,
                           0.0, 0.0, 0.0,
                           0.0, 0.0, 0.0,
                           0.0, 0.0, 0.0]

    keys = list(report.keys())
    for key in keys:
        if check_date(key):
            day = datetime.strptime(key, '%d.%m.%Y')
            months[day.month - 1] += report[key]

    _report['months'] = months

    return _report


def remove_non_numeric_chars(input_string):
    # Use a list comprehension to create a new string with allowed characters
    new_string = ''.join(c for c in input_string if c.isdigit() or c == '.' or c == '-')

    return new_string


def process_transactions(holder_id: int, ex_type='extract') -> tuple[dict[str, Union[float, str, list[float]]], str]:
    """
    This function is an improved version of the gen_timesheet_data function.
    :param holder_id: EGRPOU holder_id
    :return: a dictionary with calculations broken down by day and a line with a list of filtered transactions
    """
    patterns = Patterns()
    result: dict[str, Union[float, str]] = {}

    rows_text: str = ''
    transactions: list[DBTransaction] = DBClient().get_transactions(holder_id=holder_id, ex_type=ex_type)

    for transaction in transactions:
        if not check_date(transaction.Date) or transaction.Amount < 0:
            continue

        contains, word = if_contains_timesheet(patterns.column_A, transaction.Purpose)
        if not contains:

            if transaction.Date.strftime('%d.%m.%Y') not in result:
                result[transaction.Date.strftime('%d.%m.%Y')] = transaction.Amount
            else:
                result[transaction.Date.strftime('%d.%m.%Y')] += transaction.Amount

            fee = search_fee(patterns.column_C, transaction.Purpose)
            result[transaction.Date.strftime('%d.%m.%Y')] += fee
        else:
            rows_text += f'{transaction.Date.strftime("%d.%m.%Y")}  {transaction.Amount}  {transaction.Purpose}     filter: {word}\n'

    entrepreneur_name = DBClient().get_person(transactions[0].Holder_id)
    result['title'] = f'ФОП {entrepreneur_name.Name}'
    return result, rows_text


def gen_timesheet_data(tittle: str,
                       cells_B: list[str],
                       cells_D: list[Union[str, float]],
                       cells_F: list[str]) -> tuple[dict[str, Union[float, str, list[float]]], str]:
    """
    Deprecated
    :param tittle:
    :param cells_B:
    :param cells_D:
    :param cells_F:
    :return:
    """
    patterns = Patterns()
    result: dict[str, Union[float, str]] = {}

    rows_text: str = ''

    for cell_B, cell_D, cell_F in zip(cells_B, cells_D, cells_F):
        if check_date(cell_B):
            if type(cell_D) is str:
                sum_str = remove_non_numeric_chars(cell_D.replace(' ', '').replace(',', '.'))
                if len(sum_str) < 1 or sum_str == '-':
                    continue
                if '-' in cell_D:
                    cell_D = float(sum_str.replace('-', '')) * -1
                else:
                    cell_D = float(sum_str)

            if cell_D > 0:
                contains, word = if_contains_timesheet(patterns.column_A, cell_F)
                if not contains:

                    if cell_B not in result:
                        result[cell_B] = cell_D
                    else:
                        result[cell_B] += cell_D

                    fee = search_fee(patterns.column_C, cell_F)
                    result[cell_B] += fee
                else:
                    rows_text += f'{cell_B}  {cell_D}  {cell_F}     filter: {word}\n'

    result['title'] = tittle

    return result, rows_text


@logger.catch
def counting_revenue(data: dict[str, Union[float, str]], tax: int = 0) -> dict[str, Union[float, str]]:
    result = data

    revenue: int = 0
    for key, value in result.items():
        if 'title' not in key:
            revenue += value

    result['revenue'] = revenue
    result['tax'] = revenue * (tax / 100)

    result = quarter_identifier(result)
    result = month_sums(result)

    return result


def pars_prro_csv(prro_file: io.FileIO) -> tuple[list[str], list[Union[float, str]], list[Union[float, str]]]:
    encoding = detect_encoding(prro_file)
    separator = detect_separator(prro_file, encoding)
    file_data = add_delimiters_to_end(prro_file, delimiter=separator, encoding=encoding)

    data_frame = pd.read_csv(file_data, delimiter=separator, encoding=encoding)

    columns = data_frame.columns.values.tolist()

    try:
        if 'Дата створення' in columns[0]:
            date_column = data_frame['Дата створення'].values.tolist()
            for row_num, row in enumerate(date_column):
                if type(row) is str:
                    if re.search(r'\d*-\d*-\d* \d*:\d*:\d*', row):
                        year, month, day = row.split(' ')[0].split('-')
                        date = f'{day}.{month}.{year}'
                        date_column[row_num] = date
                elif type(row) is int:
                    real_timestamp = int(str(row)[:-9])
                    row_datetime = datetime.fromtimestamp(real_timestamp)
                    date = row_datetime.strftime('%d.%m.%Y %H:%M:%S')
                    date_column[row_num] = date

            cash_column = data_frame[columns[1]].values.tolist()
            for num, cash in enumerate(cash_column):
                cash_column[num] = 1

            sum_product = data_frame['Сума'].values.tolist()
            for num, sum_cell in enumerate(sum_product):
                if type(sum_cell) is str:
                    try:
                        sum_product[num] = float(sum_cell.replace(' ', '').replace(',', '.'))
                    except Exception as ex:
                        logger.warning(ex)

            return date_column, cash_column, sum_product
    except (TypeError, IndexError):
        raise NotHaveTemplatePRRO()

    raise NotHaveTemplatePRRO()


def parce_prro(prro_file: io.FileIO) -> tuple[list[str], list[Union[float, str]], list[Union[float, str]]]:
    try:
        data_frame = pd.read_excel(prro_file)

        columns = data_frame.columns.values.tolist()

        if "Заводський номер" in columns[0]:
            date_column = data_frame[columns[2]].values.tolist()
            for row_num, row in enumerate(date_column):
                if type(row) is str:
                    if re.search(r'\d*\.\d*\.\d* \d*:\d*:\d*', row):
                        day, month, year = row.split(' ')[0].split('.')
                        hours, minutes, seconds = row.split(' ')[1].split(':')
                        date = f'{day}.{month}.{year} {hours}:{minutes}:{seconds}'
                        date_column[row_num] = date
                elif type(row) is int:
                    logger.warning('is int')
                    real_timestamp = int(str(row)[:-9])
                    logger.warning(f'real_timestamp: {real_timestamp}')
                    row_datetime = datetime.fromtimestamp(real_timestamp)
                    logger.warning(f'row_datetime: {row_datetime}')
                    date = row_datetime.strftime('%d.%m.%Y %H:%M:%S')
                    date_column[row_num] = date

            cash_column = data_frame[columns[4]].values.tolist()
            for row_num, row in enumerate(cash_column):
                cash_column[row_num] = 1

            sum_product = data_frame[columns[8]].values.tolist()

            return date_column, cash_column, sum_product
        # ОЩАД-ПЕЙ
        elif 'Дата та час оплати' in columns[0]:
            date_column = data_frame[columns[0]].values.tolist()

            for row_num, row in enumerate(date_column):
                if type(row) is str:
                    if re.search(r'\d*.\d*.\d* \d*:\d*:\d*', row):
                        date_column[row_num] = row
                elif type(row) is int:
                    real_timestamp = int(str(row)[:-9])
                    row_datetime = datetime.fromtimestamp(real_timestamp)
                    date = row_datetime.strftime('%d.%m.%Y %H:%M:%S')
                    date_column[row_num] = date

            cash_column = data_frame[columns[5]].values.tolist()

            for row_num, row in enumerate(cash_column):
                if 'Готівка' in row:
                    cash_column[row_num] = 1
                else:
                    cash_column[row_num] = 0

            sum_product = data_frame[columns[18]].values.tolist()
            for num, sum_cell in enumerate(sum_product):
                if math.isnan(sum_cell):
                    sum_product[num] = 0.0

            return date_column, cash_column, sum_product

        # ВЧАСНО-КАССА
        elif 'ЄДРПОУ' in columns[0]:
            type_rro = 0

            date_column = data_frame[columns[2]].values.tolist()
            if type(date_column[3]) is str:
                type_rro = 1
                date_column = data_frame[columns[6]].values.tolist()

            for row_num, row in enumerate(date_column):
                if type(row) is int:
                    real_timestamp = int(str(row)[:-9])
                    row_datetime = datetime.fromtimestamp(real_timestamp)
                    date = row_datetime.strftime('%d.%m.%Y %H:%M:%S')
                    date_column[row_num] = date
            if type_rro == 0:
                cash_column = data_frame[columns[30]].values.tolist()
            else:
                cash_column = data_frame[columns[12]].values.tolist()

            if type_rro == 0:
                for num, cash in enumerate(cash_column):
                    cash_column[num] = 1
            else:
                for num, cash in enumerate(cash_column):
                    if cash == 'Картка':
                        cash_column[num] = 0
                    else:
                        cash_column[num] = 1

            sum_product = data_frame[columns[11]].values.tolist()

            return date_column, cash_column, sum_product

        elif 'Дата' in columns[0]:
            date_column = data_frame[columns[0]].values.tolist()

            for row_num, row in enumerate(date_column):
                if type(row) is str:
                    if re.search(r'\d*-\d*-\d* \d*:\d*:\d*', row):
                        year, month, day = row.split(' ')[0].split('-')
                        hours, minutes, seconds = row.split(' ')[1].split(':')
                        date = f'{day}.{month}.{year} {hours}:{minutes}:{seconds}'
                        date_column[row_num] = date

            cash_column = data_frame[columns[31]].values.tolist()

            for row_num, row in enumerate(cash_column):
                if 'Готівка' in row:
                    cash_column[row_num] = 1
                else:
                    cash_column[row_num] = 0

            sum_product = data_frame[columns[8]].values.tolist()

            return date_column, cash_column, sum_product
        elif 'Адреса каси' in columns[0]:
            date_column = data_frame[columns[1]].values.tolist()
            for row_num, row in enumerate(date_column):
                if type(row) is str:
                    if re.search(r'\d*-\d*-\d* \d*:\d*:\d*', row):
                        year, month, day = row.split(' ')[0].split('-')
                        hours, minutes, seconds = row.split(' ')[1].split(':')
                        date = f'{day}.{month}.{year} {hours}:{minutes}:{seconds}'
                        date_column[row_num] = date
                elif type(row) is int:
                    real_timestamp = int(str(row)[:-9])
                    row_datetime = datetime.fromtimestamp(real_timestamp)
                    date = row_datetime.strftime('%d.%m.%Y %H:%M:%S')
                    date_column[row_num] = date

            cash_column = data_frame[columns[18]].values.tolist()
            for row_num, row in enumerate(cash_column):
                if type(row) is str and 'Готівка' in row:
                    cash_column[row_num] = 1
                else:
                    cash_column[row_num] = 0

            sum_product = data_frame[columns[19]].values.tolist()
            for num, sum_cell in enumerate(sum_product):
                if type(sum_cell) is str and ' / ' in sum_cell:
                    sum_product[num] = float(sum_cell.split(' / ')[1])

            return date_column, cash_column, sum_product

        elif 'Облік і контроль кас' in columns[0]:
            date_column = data_frame[columns[3]].values.tolist()

            for num, date_cell in enumerate(date_column):
                if type(date_cell) is float and math.isnan(date_cell):
                    continue

                date_column[num] = f'{date_cell} 00:00:00'

            cash_column = data_frame[columns[5]].values.tolist()
            sum_product = data_frame[columns[5]].values.tolist()

            return date_column, cash_column, sum_product

        elif '#' in data_frame[columns[1]].values.tolist()[0]:
            date_column = data_frame[columns[4]].values.tolist()
            for row_num, row in enumerate(date_column):
                if type(row) is str:
                    if re.search(r'\d*-\d*-\d* \d*:\d*:\d*', row):
                        year, month, day = row.split(' ')[0].split('-')
                        hours, minutes, seconds = row.split(' ')[1].split(':')
                        date = f'{day}.{month}.{year} {hours}:{minutes}:{seconds}'
                        date_column[row_num] = date

            cash_column = data_frame[columns[12]].values.tolist()
            for num, cash in enumerate(cash_column):
                if cash == 'Готівка':
                    cash_column[num] = 1
                else:
                    cash_column[num] = 0

            sum_product = data_frame[columns[19]].values.tolist()

            return date_column, cash_column, sum_product

        elif "ID чека" in columns[0]:
            date_column = data_frame[columns[2]].values.tolist()
            for row_num, row in enumerate(date_column):
                if type(row) is str:
                    if re.search(r'\d*-\d*-\d* \d*:\d*:\d*', row):
                        year, month, day = row.split(' ')[0].split('-')
                        hours, minutes, seconds = row.split(' ')[1].split(':')
                        date = f'{day}.{month}.{year} {hours}:{minutes}:{seconds}'
                        date_column[row_num] = date
                elif type(row) is int:
                    real_timestamp = int(str(row)[:-9])
                    row_datetime = datetime.fromtimestamp(real_timestamp)
                    date = row_datetime.strftime('%d.%m.%Y %H:%M:%S')
                    date_column[row_num] = date
            cash_column = data_frame[columns[4]].values.tolist()

            transaction_types = data_frame[columns[1]].values.tolist()

            for num, t_type in enumerate(transaction_types):
                if 'RETURN' in t_type:
                    date_column[num] = ''

            for row_num, row in enumerate(cash_column):
                if type(row) is str and 'Готівка' in row or 'Накладений платіж' in row:
                    cash_column[row_num] = 1
                else:
                    cash_column[row_num] = 0

            sum_product = data_frame[columns[5]].values.tolist()

            return date_column, cash_column, sum_product
        # elif "ID чека" in columns[0]:

        elif "RegistrarNumFiscal" in columns[0]:
            date_column = data_frame[columns[3]].values.tolist()

            for row_num, row in enumerate(date_column):
                if type(row) is str:
                    if re.search(r'\d*-\d*-\d* \d*:\d*:\d*', row):
                        year, month, day = row.split(' ')[0].split('-')
                        hours, minutes, seconds = row.split(' ')[1].split(':')
                        date = f'{day}.{month}.{year} {hours}:{minutes}:{seconds}'
                        date_column[row_num] = date
                elif type(row) is int:
                    real_timestamp = int(str(row)[:-9])
                    row_datetime = datetime.fromtimestamp(real_timestamp)
                    date = row_datetime.strftime('%d.%m.%Y %H:%M:%S')
                    date_column[row_num] = date

            cash_column = data_frame[columns[4]].values.tolist()

            for row_num, row in enumerate(cash_column):
                cash_column[row_num] = 1

            sum_product = data_frame[columns[6]].values.tolist()

            return date_column, cash_column, sum_product

    except (TypeError, IndexError):
        raise NotHaveTemplatePRRO()

    raise NotHaveTemplatePRRO()


def process_prro(prro_file: io.FileIO,
                 data: dict[str, Union[float, str]],
                 mime: str,
                 file_name: str,
                 holder_id: str) -> dict[str, Union[float, str]]:
    result = data
    if mime == 'xlsx':
        date_column, cash_column, sum_product = parce_prro(prro_file)
    elif mime == 'csv':
        date_column, cash_column, sum_product = pars_prro_csv(prro_file)
    else:
        raise NotHaveTemplatePRRO()

    for date_cell, cash_cell, sum_cell in zip(date_column, cash_column, sum_product):
        prro_date = date_cell
        if type(date_cell) is str:
            prro_date = prro_date.split(' ')[0]

        if check_date(prro_date):
            if type(cash_cell) is str:
                cash_cell = float(cash_cell.replace(' ', '').replace(',', '.'))

            if type(sum_cell) is str:
                if ' / ' in sum_cell:
                    sum_cell = sum_cell.split(' / ')[0]
                sum_cell = float(sum_cell.replace(' ', '').replace(',', '.'))

            if cash_cell > 0:
                transaction = Transaction(Extract_name=file_name,
                                          Holder='',
                                          Holder_id=holder_id,
                                          Date=datetime.strptime(prro_date, '%d.%m.%Y'),
                                          Amount=sum_cell,
                                          Purpose='',
                                          Egrpou='',
                                          Type='prro',
                                          Name='',
                                          Hash=hashlib.sha256(f"{file_name}"
                                                              f"{date_cell}{sum_cell}".encode()).hexdigest())

                DBClient().add_transaction(transaction)

                #if prro_date not in result:
                #    result[prro_date] = sum_cell
                #else:
                #    result[prro_date] += sum_cell

    return result


@logger.catch
async def get_egrpou_dict(egrpou_list: list[str]) -> dict[str, bool]:
    result = {}

    for egrpou in egrpou_list:
        if egrpou in result:
            continue
        else:
            try:
                person = DBClient().get_person(int(egrpou))
                is_fop = person.Is_FOP
                result[egrpou] = is_fop
            except NotExistsPerson:
                is_fop = await get_person_info(egrpou)
                result[egrpou] = is_fop
                DBClient().add_person(int(egrpou), is_fop)

    return result


@logger.catch
async def add_list_fop_sums(data: dict[str, Union[float, str, list[str]]],
                            transactions: list[Transaction]) -> dict[str, Union[float, str, list[str]]]:
    """
    add fop transactions to data. Improved apend_fop_sums function.
    :param data: data dictionary
    :param transactions: list of Transaction objects
    :return: data + fop transactions
    """
    patterns = Patterns()

    sum_fops: dict[str, dict[str, list[Union[float, str]]]] = {}
    result: dict[str, list[str]] = {}

    for transaction in transactions:
        if transaction.Type == 'prro':
            continue

        if transaction.Amount > 0 or pd.isna(transaction.Amount):
            continue

        contains, _ = if_contains_timesheet(patterns.column_B, transaction.Purpose)
        if contains:
            continue

        if len(transaction.Egrpou) != 10:
            continue

        if not check_date(transaction.Date):
            continue

        if str(transaction.Date.month) in sum_fops:
            if f'{transaction.Egrpou}' in sum_fops[str(transaction.Date.month)]:

                sum_fops[str(transaction.Date.month)][f'{transaction.Egrpou}'][0] += transaction.Amount
            else:
                sum_fops[str(transaction.Date.month)][f'{transaction.Egrpou}'] = [transaction.Amount,
                                                                                  transaction.Name,
                                                                                  transaction.Extract_name,
                                                                                  transaction.Egrpou,
                                                                                  transaction.Holder_id,
                                                                                  transaction.Date]
        else:
            sum_fops[str(transaction.Date.month)] = {f'{transaction.Egrpou}': [transaction.Amount,
                                                                               transaction.Name,
                                                                               transaction.Extract_name,
                                                                               transaction.Egrpou,
                                                                               transaction.Holder_id,
                                                                               transaction.Date]}

    for _key in list(sum_fops.keys()):
        for key, value in sum_fops[_key].items():
            if int(key) == value[4]:
                continue

            if _key in result:
                result[_key].append(f'ЕГРПОУ: {key} СУММА: {value[0]} НАИМЕНОВАНИЕ: {value[1]}')
            else:
                result[_key] = [f'ЕГРПОУ: {key} СУММА: {value[0]} НАИМЕНОВАНИЕ: {value[1]}']
            hash_data = hashlib.sha256(f'{value[4]}{value[5].strftime("%d.%m.%Y")}{value[0]}{value[3]}{value[1]}'.encode())
            DBClient().add_fourDF(fourDFMainModel(FourDFHash=hash_data.hexdigest(),
                                                  ExtractName=value[2],
                                                  Holder_id=value[4],
                                                  Date=value[5],
                                                  Amount=value[0],
                                                  EntrepreneurID=value[3],
                                                  EntrepreneurName=value[1]))

    return {**data, **result}


@logger.catch
async def append_fop_sum(data: dict[str, Union[float, str, list[str]]],
                         list_egrpou: list[str], names: list[str],
                         sum_cells: list[Union[float, str]],
                         date_cells: list[str],
                         purpose_cells: list[str]) -> dict[str, Union[float, str, list[str]]]:
    """
    DEPRECATED
    Create list all FOP transactions
    :param data:
    :param list_egrpou:
    :param names:
    :param sum_cells:
    :param date_cells:
    :param purpose_cells:
    :return:
    """
    patterns = Patterns()

    egrpous: list[str] = []
    sum_fops: dict[str, dict[str, list[Union[float, str]]]] = {}
    result: dict[str, list[str]] = {}

    for egrpou in list_egrpou:
        if type(egrpou) is str and len(egrpou) == 10:
            egrpous.append(egrpou)
        elif type(egrpou) is int and len(f'{egrpou}') == 10:
            egrpous.append(f'{egrpou}')

    # fops: dict[str, bool] = await get_egrpou_dict(egrpous)

    for egrpou, name, sum_row, date, purpose in zip(list_egrpou, names, sum_cells, date_cells, purpose_cells):

        if (sum_row > 0 or pd.isna(sum_row)) if type(sum_row) in (float, int) else False:
            continue

        if type(purpose) is str:
            contains, _ = if_contains_timesheet(patterns.column_B, purpose)
            if contains:
                continue

        if type(f'{egrpou}') is str and len(f'{egrpou}') == 10:  # and fops[f'{egrpou}']:
            if not check_date(date):
                continue
            if date.split('.')[1] in sum_fops:
                if f'{egrpou}' in sum_fops[date.split('.')[1]]:

                    sum_fops[date.split('.')[1]][f'{egrpou}'][0] += sum_row
                else:
                    sum_fops[date.split('.')[1]][f'{egrpou}'] = [sum_row, name]
            else:
                sum_fops[date.split('.')[1]] = {f'{egrpou}': [sum_row, name]}

    for _key in list(sum_fops.keys()):
        for key, value in sum_fops[_key].items():
            if _key in result:
                result[_key].append(f'ЕГРПОУ: {key} СУММА: {value[0]} НАИМЕНОВАНИЕ: {value[1]}')
            else:
                result[_key] = [f'ЕГРПОУ: {key} СУММА: {value[0]} НАИМЕНОВАНИЕ: {value[1]}']

    return {**data, **result}


async def get_files_data(files: Union[io.FileIO, list[dict]],
                         title: str = '', holder_id: str = '') -> list[Transaction]:
    _title = f'ФОП {title}'
    date_cells = []
    sum_cells = []
    purpose_cells = []
    egrpou_cells = []
    name_cells = []

    result: list[Transaction] = []

    for extract in files:
        if extract['mime'] == 'xlsx':
            _, _date_cells, _sum_cells, _purpose_cells, _egrpou_cells, _name_cells = get_all_cells(
                extract['extract_file'],
                extract['extract_file_name'])
            date_cells = date_cells + _date_cells
            sum_cells = sum_cells + _sum_cells
            purpose_cells = purpose_cells + _purpose_cells
            egrpou_cells = egrpou_cells + _egrpou_cells
            name_cells = name_cells + _name_cells
            result = add_transactions(result, _date_cells, _sum_cells, _purpose_cells, _egrpou_cells, _name_cells,
                                      title, holder_id, extract['extract_file_name'])

        else:
            extractor = CSVExtractor(extract['extract_file'], _title)
            date_cells = date_cells + extractor.date_column
            sum_cells = sum_cells + extractor.sum_column
            purpose_cells = purpose_cells + extractor.purpose_column
            egrpou_cells = egrpou_cells + extractor.egrpou_column
            name_cells = name_cells + extractor.name_column
            result = add_transactions(result, extractor.date_column, extractor.sum_column,
                                      extractor.purpose_column, extractor.egrpou_column, extractor.name_column,
                                      title, holder_id, extract['extract_file_name'])

    # return _title, date_cells, sum_cells, purpose_cells, egrpou_cells, name_cells
    return result


def add_transactions(transactions: list[Transaction], date_cells, sum_cells,
                     purpose_cells, egrpou_cells, name_cells, title, holder_id, extract_name) -> list[Transaction]:
    for date, amount, purpose, egrpou, name in zip(date_cells, sum_cells, purpose_cells, egrpou_cells, name_cells):
        if not check_date(date):
            continue
        if pd.isna(amount):
            continue
        if pd.isna(purpose):
            purpose = ''
        if pd.isna(egrpou):
            egrpou = 0
        if pd.isna(name):
            name = ''

        transactions.append(Transaction(Extract_name=extract_name,
                                        Holder=title, Holder_id=holder_id,
                                        Date=date, Amount=amount,
                                        Purpose=purpose, Egrpou=f'{egrpou}',
                                        Type="extract", Name=name,
                                        Hash=hashlib.sha256(f"{extract_name}{title}"
                                                            f"{holder_id}{date}{amount}{purpose}"
                                                            f"{egrpou}{name}".encode()).hexdigest()))
    return transactions


async def send_transactions(transactions: list[Transaction]):
    DBClient().add_transactions(transactions)


async def get_timerange(transactions: list[Transaction]) -> tuple[datetime, datetime]:
    start_date = datetime.now()
    end_date = datetime(1990, 1, 1)
    for transaction in transactions:
        if transaction.Date < start_date:
            start_date = transaction.Date
        if transaction.Date > end_date:
            end_date = transaction.Date

    return start_date, end_date


async def month_checker(holder_id) -> list[int]:
    transactions: list[DBTransaction] = DBClient().get_dates(holder_id=holder_id)

    months: list[int] = []
    result: list[int] = []

    for transaction in transactions:
        if transaction.Date.month in months:
            continue

        months.append(transaction.Date.month)

    for month in range(0, 12):
        if month+1 in months:
            continue

        result.append(month)

    return result


async def get_timesheet_data(files: Union[io.FileIO, list[dict]], requests_type: str, mime_type: str = 'xlsx',
                             prro_files: Optional[list[list[str, io.FileIO]]] = None,
                             title: str = '',
                             holder_id: str = '',
                             prro_value: Optional[float] = None) -> tuple[dict, str, tuple[datetime, datetime], list[int]]:

    transactions: list[Transaction] = await get_files_data(files, title=title, holder_id=holder_id)
    await send_transactions(transactions)

    timerange = await get_timerange(transactions)
    timesheet_data, rows = process_transactions(int(holder_id))

    if prro_files:
        for file_name, prro_file, mime_type in prro_files:
            timesheet_data = process_prro(prro_file, timesheet_data, mime_type,
                                          file_name=file_name, holder_id=holder_id)

    transactions = DBClient().get_transactions(int(holder_id), ex_type='prro')
    for transaction in transactions:
        if transaction.Date.strftime('%d.%m.%Y') in timesheet_data:
            timesheet_data[transaction.Date.strftime('%d.%m.%Y')] += transaction.Amount
        else:
            timesheet_data[transaction.Date.strftime('%d.%m.%Y')] = transaction.Amount

    if prro_value:
        first_date = timerange[0].strftime('%d.%m.%Y')
        if first_date in timesheet_data:
            timesheet_data[first_date] += prro_value
        else:
            timesheet_data[first_date] = prro_value
        transaction = Transaction(Extract_name="Fake_PRRO",
                                  Holder='',
                                  Holder_id=holder_id,
                                  Date=timerange[0],
                                  Amount=prro_value,
                                  Purpose='',
                                  Egrpou='',
                                  Type='prro',
                                  Name='',
                                  Hash=hashlib.sha256(f"Fake_PRRO"
                                                      f"{timerange[0]}{prro_value}".encode()).hexdigest())

        DBClient().add_transaction(transaction)

    timesheet_data = counting_revenue(timesheet_data)

    if requests_type in ('timesheet', 'bok_prro'):
        # timesheet_data = await append_fop_sum(timesheet_data, egrpou_cells, name_cells, sum_cells, date_cells, purpose_cells)
        timesheet_data = await add_list_fop_sums(timesheet_data, transactions)

    lost_months: list[int] = await month_checker(holder_id)

    return timesheet_data, rows, timerange, lost_months


@logger.catch
def if_contains(patterns: list[str], string: str) -> bool:
    for pattern in patterns:
        white = pattern.split(':')[0]

        black = pattern.split(':')
        if len(black) > 1:
            black = black[1].split(',')
        else:
            black = None

        if white in string:
            if 'cmps800' in string:
                return False

            if black:
                for black_pattern in black:
                    if black_pattern in string:
                        return False
            return True

    return False


@logger.catch
def sum_cells(cells_B: list[str], cells_D: list[Union[str, float]], cells_F: list[str], tax: int = 0) -> dict[
    str, Union[float, str]]:
    patterns = Patterns()
    result: dict[str, Union[float, str]] = {'positives': 0.0,
                                            'negatives': 0.0}

    for cell_B, cell_D, cell_F in zip(cells_B, cells_D, cells_F):

        # if type(cell_D) in (float, int) and cell_D > 0:
        #    if not if_contains(patterns.blacklist, cell_F):
        #        result['positives'] += cell_D

        if type(cell_D) in (float, int) and cell_D < 0:
            if if_contains(patterns.whitelist_minus, cell_F):
                result['negatives'] += cell_D

        if check_date(cell_B):

            if if_contains(patterns.whitelist, cell_F):
                if type(cell_D) in (float, int) and cell_D > 0:
                    result['positives'] += cell_D

                if cell_B not in result:
                    result[cell_B] = cell_D
                else:
                    result[cell_B] += cell_D

            elif check_cmps_800(cell_F):
                if type(cell_D) in (float, int) and cell_D > 0:
                    result['positives'] += cell_D

                if cell_B not in result:
                    result[cell_B] = cell_D
                else:
                    result[cell_B] += cell_D

                fee = get_fee(cell_F)
                result[cell_B] += fee

                if type(cell_D) in (float, int) and cell_D > 0:
                    result['positives'] += fee

                result[cell_B] = round(result[cell_B], 2)

    sums: int = 0
    for key, value in result.items():
        if key not in ('positives', 'negatives'):
            sums += value

    result['revenue'] = sums
    result['tax'] = sums * (tax / 100)

    return result


@logger.catch
def check_date(string) -> bool:
    if isinstance(string, datetime):
        return True

    if type(string) is str:
        pattern = re.compile(r'^\d\d\.\d\d\.\d\d\d\d$')
        match = pattern.search(string)
        if match:
            return True
        else:
            return False
    return False


@logger.catch
def check_transfers(string: str) -> bool:
    if type(string) is str:
        pattern = re.compile(r'.*Перекази:.*')
        match = pattern.search(string)
        if match:
            return True
        else:
            return False
    return False


@logger.catch
def check_cmps_800(string: str) -> bool:
    if type(string) is str:
        pattern = re.compile(r'cmps: 800.*')
        match = pattern.search(string)
        if match:
            return True
        else:
            return False
    return False


@logger.catch
def get_fee(raw_string: str) -> float:
    fee = re.search(r'cmps: 800.* (\d*\.\d*)грн', raw_string)[1]
    return float(fee)


@logger.catch
def get_tittle(raw_tittle: str) -> str:
    tittle = re.search(r'.*"(.*)".*', raw_tittle)[1]
    return tittle


@logger.catch
def get_result(file_path: Union[str, io.FileIO]) -> dict[str, Union[float, str]]:
    tittle, cells_B, cells_D, cells_F, egrpou_cells, name_cells = get_all_cells(file_path)
    result = sum_cells(cells_B, cells_D, cells_F)
    result['title'] = get_tittle(tittle)
    return result


if __name__ == '__main__':
    # test_file_path = r'C:\Users\valbo\Downloads\Telegram Desktop\Для книги\виписка червень (1).xls'
    # test_file_name = 'test_file_name'
    #
    # result, _ = asyncio.run(get_timesheet_data(test_file_path, test_file_name, 'timesheet'))
    #
    # print((result))
    import os

    folder_path = r"C:\Users\valbo\Downloads\csv"  # Замените на путь к вашей папке

    # Получить список файлов в папке
    # file_list = os.listdir(folder_path)
    #
    ## Теперь переменная file_list содержит список файлов в указанной папке
    # for file_name in file_list:
    #    with open(f'{folder_path}\{file_name}', 'rb') as bin_file:
    #        print(detect_encoding(bin_file))
    #
    with open(f'{folder_path}\\0000003227761776.csv', 'r', encoding='WINDOWS-1251') as file:
        print(file.read())
