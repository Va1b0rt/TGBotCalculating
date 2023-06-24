import io
import re
from typing import Union

import pandas as pd

from logger import Logger


cls_logger = Logger()
logger = cls_logger.get_logger


@logger.catch
def get_all_cells(file_path: str):
    data_frame = pd.read_excel(file_path)

    tittle = data_frame['Unnamed: 0'].values.tolist()[0]

    column_b_values = data_frame['Unnamed: 1'].values.tolist()
    column_d_values = data_frame['Unnamed: 3'].values.tolist()
    column_f_values = data_frame['Unnamed: 5'].values.tolist()

    return tittle, column_b_values, column_d_values, column_f_values


@logger.catch
def sum_cells(cells_B: list[str], cells_D: list[Union[str, float]], cells_F: list[str], tax: int = 0) -> dict[str, Union[float, str]]:

    result: dict[str, Union[float, str]] = {'positives': 0.0}
    for cell_B, cell_D, cell_F in zip(cells_B, cells_D, cells_F):
        if type(cell_D) in (float, int) and cell_D > 0:
            if "Готiвковi надходження власних коштiв" not in cell_F and "Повернення помилково перерахованих коштiв" not in cell_F:
                result['positives'] += cell_D

        if check_date(cell_B):

            if check_transfers(cell_F):
                if cell_B not in result:
                    result[cell_B] = cell_D
                else:
                    result[cell_B] += cell_D

            elif check_cmps_800(cell_F):
                if cell_B not in result:
                    result[cell_B] = cell_D
                else:
                    result[cell_B] += cell_D
                fee = get_fee(cell_F)
                result[cell_B] += fee
                result[cell_B] = round(result[cell_B], 2)

    sum: int = 0
    for key, value in result.items():
        if key != 'positives':
            sum += value

    result['revenue'] = sum
    result['tax'] = sum * (tax/100)

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
