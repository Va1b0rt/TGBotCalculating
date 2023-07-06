import datetime
import io
import re
from typing import Union

import pandas as pd

from logger import Logger
from cloud_sheets import Patterns

cls_logger = Logger()
logger = cls_logger.get_logger


@logger.catch
def get_all_cells(file_path: Union[str, io.FileIO], filename: str):
    data_frame = pd.read_excel(file_path)

    columns = data_frame.columns.values.tolist()
    test = data_frame[columns[0]].values.tolist()

    # 1
    if data_frame[columns[0]].values.tolist()[2] == '№':
        tittle = re.search(r'.*"(.*)".*', data_frame[columns[0]].values.tolist()[0])[1]
        date_column = data_frame[columns[1]].values.tolist()
        sum_column = data_frame[columns[3]].values.tolist()
        purpose_column = data_frame[columns[5]].values.tolist()
        return tittle, date_column, sum_column, purpose_column
    # TASCOMBANK
    elif data_frame[columns[0]].values.tolist()[0] == '№':
        tittle = re.search(r', (.*) з', columns[0])[1]

        date_column = data_frame[columns[1]].values.tolist()
        for row_num, date in enumerate(date_column):
            if type(date) is datetime.datetime:
                date_column[row_num] = date.strftime('%d.%m.%Y')

        sum_column = data_frame[columns[2]].values.tolist()
        purpose_column = data_frame[columns[4]].values.tolist()
        return tittle, date_column, sum_column, purpose_column
    # MONO
    elif 'Клієнт:' in columns[0]:

        tittle = columns[0].replace('Клієнт:', '')
        date_column = data_frame[columns[0]].values.tolist()
        for row_num, row in enumerate(date_column):
            if type(row) is str:
                if re.search(r'\d*.\d*.\d* \d*:\d*:\d*', row):
                    date_column[row_num] = row.split(' ')[0]

        sum_column = data_frame[columns[5]].values.tolist()
        purpose_column = data_frame[columns[1]].values.tolist()
        return tittle, date_column, sum_column, purpose_column
    #  A-BANK
    elif 'Дата' in columns[0]:
        tittle = exclude_non_cyrillic(filename)
        date_column = data_frame[columns[0]].values.tolist()
        sum_column = data_frame[columns[7]].values.tolist()

        purpose_column = data_frame[columns[6]].values.tolist()

        for num, purpose in enumerate(purpose_column):
            if 'Відшкодування за еквайринг' in purpose:
                match = re.search(r'\d+\.\d+', purpose)
                if match:
                    sum_column[num] = float(match[0])

        return tittle, date_column, sum_column, purpose_column


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
            if pattern.lower() in string.lower():
                return True, pattern

    return False, ''


@logger.catch
def search_fee(patterns: list[str], raw_string: str) -> float:
    for pattern in patterns:
        match = re.search(pattern.lower() + r'[., ]*(\d*\.\d*).', raw_string.lower())

        if match:
            return float(match[1])

    return float(0.00)


@logger.catch
def quarter_identifier(report: dict[str, Union[float, str]]) -> dict[str, Union[float, str]]:
    _report = report
    quarters: list[float] = [0.0, 0.0, 0.0, 0.0]

    keys = list(report.keys())
    for key in keys:
        if check_date(key):
            day = datetime.datetime.strptime(key, '%d.%m.%Y')
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
            day = datetime.datetime.strptime(key, '%d.%m.%Y')
            months[day.month - 1] += report[key]

    _report['months'] = months

    return _report


@logger.catch
def gen_timesheet_data(tittle: str, cells_B: list[str], cells_D: list[Union[str, float]], cells_F: list[str],
                       tax: int = 0) -> tuple[dict[str, Union[float, str, list[float]]], str]:
    patterns = Patterns()
    result: dict[str, Union[float, str]] = {}
    rows_text: str = ''

    for cell_B, cell_D, cell_F in zip(cells_B, cells_D, cells_F):
        if check_date(cell_B):
            if type(cell_D) is str:
                cell_D = float(cell_D.replace(' ', '').replace(',', '.'))

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

    sum: int = 0
    for key, value in result.items():
        sum += value

    result['revenue'] = sum
    result['tax'] = sum * (tax / 100)

    result['tittle'] = tittle

    result = quarter_identifier(result)
    result = month_sums(result)

    return result, rows_text


@logger.catch
def get_timesheet_data(file_path: Union[str, io.FileIO], filename: str) -> tuple[dict[str, Union[float, str]], str]:
    tittle, cells_B, cells_D, cells_F = get_all_cells(file_path, filename)
    timesheet_data, rows = gen_timesheet_data(tittle, cells_B, cells_D, cells_F)
    return timesheet_data, rows


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

    sum: int = 0
    for key, value in result.items():
        if key not in ('positives', 'negatives'):
            sum += value

    result['revenue'] = sum
    result['tax'] = sum * (tax / 100)

    return result


@logger.catch
def check_date(string: str) -> bool:
    if type(string) is str:
        pattern = re.compile(r'\d\d\.\d\d\.\d\d\d\d')
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
    tittle, cells_B, cells_D, cells_F = get_all_cells(file_path)
    result = sum_cells(cells_B, cells_D, cells_F)
    result['tittle'] = get_tittle(tittle)
    return result


if __name__ == '__main__':
    fee = search_fee(['ком бан', 'комісія банку'],
                     'Відшкодування за еквайринг “шаурма сити”: 7 операцій на суму 1150.00 грн, повернень на суму 0.00 грн, комісія банку 19.55 грн.')
    sum = 1130.45
    print(fee + sum)
