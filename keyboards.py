from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

button_timesheet_acquiring = InlineKeyboardButton('Табель (эквайринг)', callback_data='button_timesheet_acquiring')
button_extract = InlineKeyboardButton('Выписка', callback_data='button_extract')

keyboard_main = InlineKeyboardMarkup() \
    .row(button_timesheet_acquiring, button_extract)

