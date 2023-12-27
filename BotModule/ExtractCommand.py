import io

from aiogram.types import Message, CallbackQuery, ContentType, ParseMode

from BotModule import dp, bot, logger
from BotModule.States import StatesMenu
from calculating import get_timesheet_data, get_result


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
