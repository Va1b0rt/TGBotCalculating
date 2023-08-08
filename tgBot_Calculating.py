import atexit
import io

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.files import JSONStorage
from aiogram.dispatcher import FSMContext
from aiogram.types import ContentType, Message, CallbackQuery, ParseMode

from calculating import get_result, get_timesheet_data
from XLAssembler import TableAssembler
from cloud_sheets import Employers
from logger import Logger
from config import BOT_API_TOKEN
from states import StatesMenu
from tables.settlement_payment import SettlementPayment
from tables.working_hour_sheet import AppearanceOTWHSheet

cls_logger = Logger()
logger = cls_logger.get_logger

storage = JSONStorage('./storage/storage.json')
bot = Bot(token=BOT_API_TOKEN)
dp = Dispatcher(bot, storage=storage)


async def save_out():
    dp.stop_polling()
    await dp.storage.close()
    await dp.storage.wait_closed()
    return


atexit.register(save_out)


@dp.message_handler(commands=['start'], state='*')
async def start_message_command(message: Message):
    await StatesMenu.main.set()
    await bot.send_message(message.chat.id,
                           'Вас приветствует бот для расчёта данных из выписок.'
                           )


@dp.message_handler(commands=['timesheet'], state='*')
async def start_message_command(message: Message):
    await StatesMenu.timesheet_acquiring.set()
    await bot.send_message(message.chat.id, 'Ожидаю файл выписки.')


@dp.callback_query_handler(lambda call: call.data == "button_timesheet_acquiring", state=StatesMenu.main)
async def button_upload(call: CallbackQuery):
    await StatesMenu.timesheet_acquiring.set()
    await bot.send_message(call.message.chat.id, 'Ожидаю файл выписки.')


@logger.catch
@dp.message_handler(content_types=ContentType.DOCUMENT, state=StatesMenu.timesheet_acquiring)
async def handle_document(message: Message):
    document = message.document
    if document.mime_type in ('application/vnd.ms-excel', 'application/x-msexcel',
                              'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'):
        await message.answer('Получен XLS-файл. Обрабатываем...')
        file_id = document.file_id
        file_info = await bot.get_file(file_id)
        file_path = file_info.file_path
        file = await bot.download_file(file_path)
        file_name = message.document.file_name.replace('.xlsx', '').replace('.xls', '')
        result, _ = await get_timesheet_data(file, file_name, 'timesheet')

        ta = TableAssembler(result)
        result_tables, result_fops = ta.get_bytes()

        for result in result_tables:

            await bot.send_document(message.chat.id, types.InputFile(result, filename='RESULT.xls'))

        if result_fops:
            await bot.send_document(message.chat.id, types.InputFile(result_fops, filename='RESULT.txt'))

    else:
        await message.answer('Прикреплённый файл не является XLS-файлом')
        logger.warning('Прикреплённый файл не является XLS-файлом')

    await StatesMenu.main.set()


@dp.message_handler(commands=['extract'], state='*')
async def start_message_command(message: Message):
    await StatesMenu.extract.set()
    await bot.send_message(message.chat.id, 'Ожидаю файл выписки.')


@dp.callback_query_handler(lambda call: call.data == "button_extract", state=StatesMenu.main)
async def button_upload(call: CallbackQuery):
    await StatesMenu.extract.set()
    await bot.send_message(call.message.chat.id, 'Ожидаю файл выписки.')


@logger.catch
@dp.message_handler(content_types=ContentType.DOCUMENT, state=StatesMenu.extract)
async def handle_document(message: Message):
    document = message.document
    if document.mime_type in ('application/vnd.ms-excel', 'application/x-msexcel',
                              'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'):
        await message.answer('Получен XLS-файл. Обрабатываем...')
        file_id = document.file_id
        file_info = await bot.get_file(file_id)
        file_path = file_info.file_path
        file = await bot.download_file(file_path)
        file_name = message.document.file_name.replace('.xlsx', '').replace('.xls', '')
        result, rows = await get_timesheet_data(file, file_name, 'extract')

        rows_io = io.BytesIO()
        rows_io.write(rows.encode('utf-8'))
        rows_io.seek(0)

        msg = f'Всего: <code>{result["revenue"] if result.get("revenue") else "0.00"}</code>\n' \
              f'1 Квартал: <code>{result["quarter_1"] if result.get("quarter_1") else "0.00"}</code>\n' \
              f'2 Квартал: <code>{result["quarter_2"] if result.get("quarter_2") else "0.00"}</code>\n' \
              f'3 Квартал: <code>{result["quarter_3"] if result.get("quarter_3") else "0.00"}</code>\n' \
              f'4 Квартал: <code>{result["quarter_4"] if result.get("quarter_4") else "0.00"}</code>\n'

        await bot.send_message(message.chat.id,
                               msg,
                               parse_mode=ParseMode.HTML)

    else:
        await message.answer('Прикреплённый файл не является XLS-файлом')
        logger.warning('Прикреплённый файл не является XLS-файлом')

    await StatesMenu.main.set()


@dp.message_handler(commands=['extract_all'], state='*')
async def start_message_command(message: Message):
    await StatesMenu.extract_all.set()
    await bot.send_message(message.chat.id, 'Ожидаю файл выписки.')


@logger.catch
@dp.message_handler(content_types=ContentType.DOCUMENT, state=StatesMenu.extract_all)
async def handle_document(message: Message):
    document = message.document
    if document.mime_type in ('application/vnd.ms-excel', 'application/x-msexcel',
                              'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'):
        await message.answer('Получен XLS-файл. Обрабатываем...')
        file_id = document.file_id
        file_info = await bot.get_file(file_id)
        file_path = file_info.file_path
        file = await bot.download_file(file_path)
        result = get_result(file)

        await bot.send_message(message.chat.id,
                               f'Всего: <code>{result["positives"] if result.get("positives") else "0.00"}</code>\n'
                               f'Затраты: <code>{result["negatives"] if result.get("negatives") else "0.00"}</code>',
                               parse_mode=ParseMode.HTML)

    else:
        await message.answer('Прикреплённый файл не является XLS-файлом')
        logger.warning('Прикреплённый файл не является XLS-файлом')

    await StatesMenu.main.set()


@dp.message_handler(commands=['extract_test'], state='*')
async def start_message_command(message: Message):
    await StatesMenu.extract_test.set()
    await bot.send_message(message.chat.id, 'Ожидаю файл выписки.')


@logger.catch
@dp.message_handler(content_types=ContentType.DOCUMENT, state=StatesMenu.extract_test)
async def handle_document(message: Message):
    document = message.document
    if document.mime_type in ('application/vnd.ms-excel', 'application/x-msexcel',
                              'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'):
        await message.answer('Получен XLS-файл. Обрабатываем...')
        file_id = document.file_id
        file_info = await bot.get_file(file_id)
        file_path = file_info.file_path
        file = await bot.download_file(file_path)
        file_name = message.document.file_name.replace('.xlsx', '').replace('.xls', '')
        result, rows = await get_timesheet_data(file, file_name, 'extract')

        rows_io = io.BytesIO()
        rows_io.write(rows.encode('utf-8'))
        rows_io.seek(0)

        msg = f'Всего: <code>{result["revenue"] if result.get("revenue") else "0.00"}</code>\n' \
              f'1 Квартал: <code>{result["quarter_1"] if result.get("quarter_1") else "0.00"}</code>\n' \
              f'2 Квартал: <code>{result["quarter_2"] if result.get("quarter_2") else "0.00"}</code>\n' \
              f'3 Квартал: <code>{result["quarter_3"] if result.get("quarter_3") else "0.00"}</code>\n' \
              f'4 Квартал: <code>{result["quarter_4"] if result.get("quarter_4") else "0.00"}</code>\n'

        await bot.send_message(message.chat.id,
                               msg,
                               parse_mode=ParseMode.HTML)
        await bot.send_document(message.chat.id,
                                types.InputFile(rows_io, filename='RESULT.txt'))

    else:
        await message.answer('Прикреплённый файл не является XLS-файлом')
        logger.warning('Прикреплённый файл не является XLS-файлом')

    await StatesMenu.main.set()


@logger.catch
@dp.message_handler(commands=['bok_prro'], state='*')
async def start_message_command(message: Message):
    await StatesMenu.bok_prro.set()
    await bot.send_message(message.chat.id, 'Ожидаю файл выписки.')


@logger.catch
@dp.message_handler(content_types=ContentType.DOCUMENT, state=StatesMenu.bok_prro)
async def handle_extract(message: Message, state: FSMContext):
    document = message.document
    if document.mime_type in ('application/vnd.ms-excel', 'application/x-msexcel',
                              'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'):
        await message.answer('Получен файл выписки. Обрабатываем...')
        async with state.proxy() as data:
            data['extract'] = document

        await StatesMenu.next()
        await bot.send_message(message.chat.id, 'Ожидаю файл ПРРО')


@logger.catch
@dp.message_handler(content_types=ContentType.DOCUMENT, state=StatesMenu.bok_prro_2)
async def handle_extract(message: Message, state: FSMContext):
    prro = message.document
    if prro.mime_type in ('application/vnd.ms-excel', 'application/x-msexcel',
                          'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'):
        await message.answer('Получен файл ПРРО. Обрабатываем...')
        async with state.proxy() as data:
            extract = data['extract']

            extract_file_id = extract.file_id
            extract_file_info = await bot.get_file(extract_file_id)
            extract_file_path = extract_file_info.file_path
            extract_file = await bot.download_file(extract_file_path)
            extract_file_name = message.document.file_name.replace('.xlsx', '').replace('.xls', '')

            prro_file_id = prro.file_id
            prro_file_info = await bot.get_file(prro_file_id)
            prro_file_path = prro_file_info.file_path
            prro_file = await bot.download_file(prro_file_path)

            result, rows = await get_timesheet_data(extract_file, extract_file_name, 'bok_prro', prro_file=prro_file)

            ta = TableAssembler(result)
            result_tables, result_fops = ta.get_bytes()

            for _result in result_tables:
                await bot.send_document(message.chat.id, types.InputFile(_result, filename='RESULT.xls'))

            if result_fops:
                await bot.send_document(message.chat.id, types.InputFile(result_fops, filename='RESULT.txt'))
    else:
        await message.answer('Прикреплённый файл не является XLS-файлом')
        logger.warning('Прикреплённый файл не является XLS-файлом')

    await state.finish()
    await StatesMenu.main.set()


async def send_document_group(chat_id, documents, title: str):
    media = []
    for num, document_data in enumerate(documents):
        message = ''
        file_name = f'Табель 7 {title}.xlsx'
        if num == 0:
            message = f'{title}'
            file_name = f'Расчётно-платёжная {title}.xlsx'

        media.append(types.InputMediaDocument(media=types.InputFile(document_data, filename=file_name), caption=message))

    await bot.send_media_group(chat_id=chat_id, media=media)


@logger.catch
@dp.message_handler(commands=['test_command'], state='*')
async def start_message_command(message: Message):
    await StatesMenu.test_state.set()
    await bot.send_message(message.chat.id, 'Генерируем пакет документов.')

    employers = Employers()

    for employer in employers.get_employers():
        sp = SettlementPayment(employer)
        sp_doc = sp.get_bytes()

        aowhs = AppearanceOTWHSheet(employer)
        aowhs_doc = aowhs.get_bytes()

        await send_document_group(message.chat.id, [sp_doc, aowhs_doc], employer.name)


if __name__ == "__main__":
    try:
        executor.start_polling(dp, skip_updates=True)
    except Exception as ex:
        logger.critical(ex)

    input("Нажмите Enter для завершения программы...")
