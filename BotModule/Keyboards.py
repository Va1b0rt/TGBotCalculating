import hashlib
import base64
import math

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from DBAPI.DBClient import DBClient
from DBAPI.DBExceptions import NotExistsFourDF
from DBAPI.Models import Persons
from cloud_sheets import Entrepreneurs
from utils.StringCompresser import shorten_name

button_timesheet_acquiring = InlineKeyboardButton('Табель (эквайринг)', callback_data='button_timesheet_acquiring')
button_extract = InlineKeyboardButton('Выписка', callback_data='button_extract')

keyboard_main = InlineKeyboardMarkup() \
    .row(button_timesheet_acquiring, button_extract)

# TIMESHEET
button_handle_extracts_timesheet = InlineKeyboardButton('Обработать', callback_data='button_handle_extracts_timesheet')
keyboard_handle_extracts_timesheet = InlineKeyboardMarkup() \
    .row(button_handle_extracts_timesheet)

# BOOK PRRO
button_handle_extracts = InlineKeyboardButton('Обработать', callback_data='button_handle_extracts')
keyboard_handle_extracts = InlineKeyboardMarkup() \
    .row(button_handle_extracts)

button_handle_prro = InlineKeyboardButton('Обработать', callback_data='button_handle_prro')
keyboard_handle_prro = InlineKeyboardMarkup() \
    .row(button_handle_prro)


# EMPTY BOOK
months = [
    "01 - Январь(Січень)",
    "02 - Февраль(Лютий)",
    "03 - Март(Березень)",
    "04 - Апрель(Квітень)",
    "05 - Май(Травень)",
    "06 - Июнь(Червень)",
    "07 - Июль(Липень)",
    "08 - Август(Серпень)",
    "09 - Сентябрь(Вересень)",
    "10 - Октябрь(Жовтень)",
    "11 - Ноябрь(Листопад)",
    "12 - Декабрь(Грудень)"
]

months_buttons = []
for month in months:
    months_buttons.append(InlineKeyboardButton(month, callback_data=f'month_{month:2}'))

month_keyboard = InlineKeyboardMarkup() \
    .row(months_buttons[0], months_buttons[1], months_buttons[2]) \
    .row(months_buttons[3], months_buttons[4], months_buttons[5]) \
    .row(months_buttons[6], months_buttons[7], months_buttons[8]) \
    .row(months_buttons[9], months_buttons[10], months_buttons[11])


def entrepreneurs_menu(entrepreneurs: Entrepreneurs, name: str = '', remover: int = 0) -> InlineKeyboardMarkup:
    if remover >= len(entrepreneurs): remover -= 9

    buttons = []

    for count, a in enumerate(range(remover, len(entrepreneurs))):

        if count < 9:
            names = entrepreneurs.keys
            fop_ids = entrepreneurs.values
            buttons.append(InlineKeyboardButton(names[a], callback_data=f'fop_{names[a]}_{fop_ids[a]}'))

    if len(entrepreneurs) > 9 > remover:
        buttons.append(InlineKeyboardButton(f"💎 1/{math.ceil(len(entrepreneurs) / 9) - 1} 💎"
                                            , callback_data=f'...'))
        buttons.append(InlineKeyboardButton("Далее 👉",
                                            callback_data=f"entrepreneurs_menu:{remover + 9}"))

    elif remover + 10 >= len(entrepreneurs):
        buttons.append(InlineKeyboardButton("👈 Назад", callback_data=f"entrepreneurs_menu:{remover - 9}"))
        buttons.append(InlineKeyboardButton(f"💎 {str(remover + 9)[:-1]}/{math.ceil(len(entrepreneurs) / 9)-1} 💎",
                                            callback_data="..."))

    else:
        buttons.append(InlineKeyboardButton("👈 Назад", callback_data=f"entrepreneurs_menu:{remover - 9}"))
        buttons.append(InlineKeyboardButton(f"💎 {str(remover + 9)[:-1]}/{math.ceil(len(entrepreneurs) / 9)-1} 💎",
                                            callback_data="..."))
        buttons.append(InlineKeyboardButton("Далее 👉",
                                            callback_data=f"entrepreneurs_menu:{remover + 9}"))

    entrepreneurs_keyboard = InlineKeyboardMarkup()
    entrepreneurs_keyboard.add(*buttons)

    return entrepreneurs_keyboard


# ENTREPRENEURS MENU
def entrepreneurs_keyboard(entrepreneurs: list[Persons]) -> InlineKeyboardMarkup:
    buttons = []

    for entrepreneur in entrepreneurs:
        buttons.append(InlineKeyboardButton(entrepreneur.Name,
                                            callback_data=f'fop_{shorten_name(entrepreneur.Name)}_'
                                                          f'{entrepreneur.Person_ID}'))

    return InlineKeyboardMarkup().add(*buttons)


def extracts_keyboard(extracts: list[dict]) -> InlineKeyboardMarkup:
    buttons = []
    for extract in extracts:
        hashed_data = hashlib.sha256(extract['name'].encode()).digest()
        short_hash = base64.urlsafe_b64encode(hashed_data)[:64].decode()
        buttons.append(
            InlineKeyboardButton(f"{extract['month']}_{extract['name']}"[:20], callback_data=f'ex_{short_hash}'))

    return InlineKeyboardMarkup() \
        .add(*buttons) \
        .row(InlineKeyboardButton('Назад', callback_data='back_extracts_menu'))


def extract_details_keyboard(extract_name: str, holder_id: int) -> InlineKeyboardMarkup:
    try:
        fourDFs = DBClient().get_fourDF(holder_id, extract_name)

        buttons = [
            InlineKeyboardButton('Показать 4ДФ', callback_data=f'fourDF_{extract_name}'),
            InlineKeyboardButton('Удалить', callback_data=f'delete_extract_{extract_name}'),
            InlineKeyboardButton('Назад', callback_data='back_extracts_details')
        ]
    except NotExistsFourDF:
        buttons = [
            InlineKeyboardButton('Удалить', callback_data=f'delete_extract_{extract_name}'),
            InlineKeyboardButton('Назад', callback_data='back_extracts_details')
        ]

    return InlineKeyboardMarkup().add(*buttons)


# END ENTREPRENEURS MENU


# ADMIN MENU
def get_menu() -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton('Пользователи', callback_data=f'userlist'),
        InlineKeyboardButton('Добавить', callback_data=f'addUser')
    ]

    return InlineKeyboardMarkup().add(*buttons)


def get_users(userList) -> InlineKeyboardMarkup:
    buttons = []

    for user in userList:
        buttons.append(InlineKeyboardButton(f'{user[1]}({user[0]})', callback_data=f'user_{user[0]}'))

    return InlineKeyboardMarkup().add(*buttons)


def user_detail_keyboard(user) -> InlineKeyboardMarkup:
    buttons = [InlineKeyboardButton('Изменить имя', callback_data=f'change_name')]
    button_admin_text = "Дать права" if not user.isAdmin else "Лишить прав"
    if not user.topAdmin:
        buttons.append(InlineKeyboardButton(button_admin_text, callback_data=f'change_admin'))
    buttons.append(InlineKeyboardButton("Назад", callback_data=f'backTo_userList'))

    return InlineKeyboardMarkup().add(*buttons)
# END ADMIN MENU
