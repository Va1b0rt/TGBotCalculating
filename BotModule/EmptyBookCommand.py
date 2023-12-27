from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery, ContentType, InputFile

from BotModule import logger, dp, bot, commands
from BotModule.States import StatesMenu
from XLAssembler import TableAssembler
from keyboards import month_keyboard


@logger.catch
@dp.message_handler(commands=['get_empty_book'], state='*')
async def empty_book_command(message: Message, state: FSMContext):
    #await StatesMenu.bok_prro.set()

    async with state.proxy() as data:
        data.clear()

    await StatesMenu.empty_book_change_month.set()
    await bot.send_message(message.chat.id, 'Выберите месяц:', reply_markup=month_keyboard)


@logger.catch
@dp.callback_query_handler(lambda call: call.data.startswith("month_"), state=StatesMenu.empty_book_change_month)
async def set_name(call: CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['month'] = call.data.replace('month_', '')

    await StatesMenu.change_name.set()
    await bot.send_message(call.message.chat.id, 'Укажите имя владельца выписки:')


@logger.catch
@dp.message_handler(lambda message: message.text not in commands,
                    content_types=ContentType.TEXT, state=StatesMenu.change_name)
async def generate_empty_extract(message: Message, state: FSMContext):
    title = message.text
    async with state.proxy() as data:
        month = data['month']

    ta = TableAssembler(_tittle=title, _month=month)
    result_tables, _ = ta.get_bytes()

    for _result in result_tables:
        await bot.send_document(message.chat.id,
                                InputFile(_result["workbooks_bytes"],
                                          filename=f'Книга за {_result["workbooks_month"]}_'
                                                   f'{data["title"]}.xls'))
