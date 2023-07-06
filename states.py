from aiogram.dispatcher.filters.state import StatesGroup, State


class StatesMenu(StatesGroup):
    main = State()
    timesheet_acquiring = State()
    extract = State()
    extract_all = State()
    extract_test = State()
