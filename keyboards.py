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
