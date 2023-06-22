from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.files import JSONStorage
from aiogram.types import ContentType, Message, CallbackQuery, ParseMode

from calculating import get_result
from XLAssembler import TableAssembler
from logger import Logger
from config import BOT_API_TOKEN
from keyboards import keyboard_main
from states import StatesMenu

cls_logger = Logger()
logger = cls_logger.get_logger

storage = JSONStorage('./storage/storage.json')
bot = Bot(token=BOT_API_TOKEN)
dp = Dispatcher(bot, storage=storage)


@dp.message_handler(commands=['start'], state='*')
async def start_message_command(message: Message):
    await StatesMenu.main.set()
    await bot.send_message(message.chat.id,
                           'Вас приветствует бот для расчёта данных из выписок.',
                           reply_markup=keyboard_main)


@dp.callback_query_handler(lambda call: call.data == "button_timesheet_acquiring", state=StatesMenu.main)
async def button_upload(call: CallbackQuery):
    await StatesMenu.timesheet_acquiring.set()
    await bot.send_message(call.message.chat.id, 'Ожидаю файл выписки.')


@logger.catch
@dp.message_handler(content_types=ContentType.DOCUMENT, state=StatesMenu.timesheet_acquiring)
async def handle_document(message: Message):
    document = message.document
    if document.mime_type in ('application/vnd.ms-excel', 'application/x-msexcel'):
        await message.answer('Получен XLS-файл. Обрабатываем...')
        file_id = document.file_id
        file_info = await bot.get_file(file_id)
        file_path = file_info.file_path
        file = await bot.download_file(file_path)
        result = get_result(file)

        ta = TableAssembler(result)
        result_table = ta.get_bytes()

        await bot.send_document(message.chat.id, types.InputFile(result_table, filename='RESULT.xls'),
                                reply_markup=keyboard_main)
        # await message.answer(f'Искомое значение: <code>{result}</code>', parse_mode=ParseMode.HTML)

    else:
        await message.answer('Прикреплённый файл не является XLS-файлом', reply_markup=keyboard_main)
        logger.warning('Прикреплённый файл не является XLS-файлом')

    await StatesMenu.main.set()


@dp.callback_query_handler(lambda call: call.data == "button_extract", state=StatesMenu.main)
async def button_upload(call: CallbackQuery):
    await StatesMenu.extract.set()
    await bot.send_message(call.message.chat.id, 'Ожидаю файл выписки.')


@logger.catch
@dp.message_handler(content_types=ContentType.DOCUMENT, state=StatesMenu.extract)
async def handle_document(message: Message):
    document = message.document
    if document.mime_type in ('application/vnd.ms-excel', 'application/x-msexcel'):
        await message.answer('Получен XLS-файл. Обрабатываем...')
        file_id = document.file_id
        file_info = await bot.get_file(file_id)
        file_path = file_info.file_path
        file = await bot.download_file(file_path)
        result = get_result(file)

        await bot.send_message(message.chat.id, f'Всего: <code>{result["revenue"]}</code>',
                               reply_markup=keyboard_main, parse_mode=ParseMode.HTML)
        # await message.answer(f'Искомое значение: <code>{result}</code>', parse_mode=ParseMode.HTML)

    else:
        await message.answer('Прикреплённый файл не является XLS-файлом', reply_markup=keyboard_main)
        logger.warning('Прикреплённый файл не является XLS-файлом')

    await StatesMenu.main.set()


if __name__ == "__main__":
    try:
        executor.start_polling(dp, skip_updates=True)
    except Exception as ex:
        logger.critical(ex)

    input("Нажмите Enter для завершения программы...")
