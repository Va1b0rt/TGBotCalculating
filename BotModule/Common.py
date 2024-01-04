import json
from typing import Union

from BotModule import logger


@logger.catch
def get_message(state_data: dict) -> str:
    """

    :param state_data: aiogram state data
    :return: info message
    """
    extracts = ''

    if len(state_data['extracts']) > 0:
        extracts = ''.join([f"<b>{index + 1}: ✅{json.loads(doc['extract'])['file_name']}</b>\n" for index, doc in
                            enumerate(state_data['extracts'])])

    message = (f'Внесённое число выписок: <b>{len(state_data["extracts"])}</b>\n'
               f'Имя владельца: <b>"{state_data["title"] if "title" in state_data else "⚠️НЕТ ИМЕНИ⚠️"}"</b>:\n'
               f'Выписки: \n'
               f'{extracts}')

    return message


def find_entrepreneur(name: str, entrepreneurs: dict[str, str]) -> Union[bool, str]:
    """

    :param name: Entrepreneurs name
    :param entrepreneurs: dict name:id
    :return: if the entrepreneur was found, then his egrpou. if not found, return False
    """
    for entrepreneur, egrpou in entrepreneurs.items():
        if name.lower() in entrepreneur.lower():
            return f'{entrepreneur}_{egrpou}'

    return False


def get_missing_months(lost_months: list[int]) -> str:
    if lost_months:
        return f"У данного пользователя есть выписки не для всех месяцев!\n" \
               f"Отсутствующие месяцы: <b> {','.join(map(lambda month: str(month+1), lost_months))}</b>"

    return ''
