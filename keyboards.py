from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

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

month_keyboard = InlineKeyboardMarkup()\
    .row(months_buttons[0], months_buttons[1], months_buttons[2])\
    .row(months_buttons[3], months_buttons[4], months_buttons[5])\
    .row(months_buttons[6], months_buttons[7], months_buttons[8])\
    .row(months_buttons[9], months_buttons[10], months_buttons[11])

