from aiogram.dispatcher.filters.state import StatesGroup, State


class StatesMenu(StatesGroup):
    main = State()
    timesheet_acquiring = State()
    timesheet_get_extras = State()
    extract = State()
    extract_all = State()
    extract_test = State()
    book_prro_get_extracts = State()
    bok_prro = State()
    bok_prro_2 = State()
    test_state = State()
    tittle_question = State()
    tittle_question_prro = State()
