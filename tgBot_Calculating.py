import asyncio
import atexit
import io
import json
import os

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.files import JSONStorage
from aiogram.dispatcher import FSMContext
from aiogram.types import ContentType, Message, CallbackQuery, ParseMode

from Exceptions import NotHaveTemplate, UnknownEncoding, TemplateDoesNotFit, NotHaveTemplatePRRO, NoWorkers, \
    WorkerNotHaveWorkHours, NoColumn
from calculating import get_result, get_timesheet_data
from XLAssembler import TableAssembler
from cloud_sheets import Employers
from keyboards import button_handle_extracts, keyboard_handle_extracts, keyboard_handle_extracts_timesheet
from logger import Logger
from config import BOT_API_TOKEN
from states import StatesMenu
from tables.settlement_payment import SettlementPayment
from tables.working_hour_sheet import AppearanceOTWHSheet

cls_logger = Logger()
logger = cls_logger.get_logger

storage = JSONStorage('./storage/storage.json')
bot = Bot(token=BOT_API_TOKEN)
dp: Dispatcher = Dispatcher(bot, storage=storage)


def save_out():
    dp.stop_polling()
    asyncio.run(dp.storage.close())
    asyncio.run(dp.storage.wait_closed())
    return


atexit.register(save_out)

commands = ['/start',
            '/timesheet',
            '/extract',
            '/extract_all',
            '/extract_test',
            '/bok_prro']


@dp.message_handler(commands=['start'], state='*')
async def start_message_command(message: Message):
    await StatesMenu.main.set()
    await bot.send_message(message.chat.id,
                           'Вас приветствует бот для расчёта данных из выписок.'
                           )


# TIMESHEET
@dp.message_handler(commands=['timesheet'], state='*')
async def start_message_command(message: Message, state: FSMContext):

    async with state.proxy() as data:
        data.clear()

    await StatesMenu.timesheet_get_extras.set()
    await bot.send_message(message.chat.id, 'Ожидаю файл выписки.')


@dp.callback_query_handler(lambda call: call.data == "button_timesheet_acquiring", state=StatesMenu.main)
async def button_upload(call: CallbackQuery):
    await StatesMenu.timesheet_acquiring.set()
    await bot.send_message(call.message.chat.id, 'Ожидаю файл выписки.')


@logger.catch
@dp.message_handler(content_types=ContentType.DOCUMENT, state=StatesMenu.timesheet_get_extras)
async def handle_document(message: Message, state: FSMContext):
    document = message.document
    mime = ''

    async with state.proxy() as data:
        try:
            if hasattr(message, 'md_text'):
                data['title'] = message.md_text
        except TypeError:
            pass

        if document.mime_type in ('application/vnd.ms-excel', 'application/x-msexcel',
                                  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'):
            mime = 'xlsx'

        elif document.mime_type == 'text/csv' or document.file_name.endswith('.csv'):
            mime = 'csv'

        if 'extracts' in data:
            data['extracts'].append({
                'extract': document.as_json(),
                'mime': mime
            })
        else:
            data['extracts'] = [{
                'extract': document.as_json(),
                'mime': mime
            }]

        await message.answer(f'Получен файл «Выписки».\n'
                             f'{get_message(data)}',
                             reply_markup=keyboard_handle_extracts_timesheet,
                             parse_mode=types.ParseMode.HTML)


@logger.catch
@dp.callback_query_handler(lambda call: call.data == "button_handle_extracts_timesheet",
                           state=StatesMenu.timesheet_get_extras)
async def button_upload_timesheet(call: CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        if "title" not in data:

            await bot.send_message(call.message.chat.id,
                                   f'⚠ <b>Обратьите внимание, что вы не указали имя владельца выписки.</b> ⚠\n'
                                   'Без указания этой информации мы не сможем правильно обработать выписки.\n'
                                   f'{get_message(data)}',
                                   reply_markup=keyboard_handle_extracts_timesheet,
                                   parse_mode=types.ParseMode.HTML)
            return

    if 'extracts' in data and data['extracts']:
        await bot.edit_message_text('Обрабатываем...', call.message.chat.id, call.message.message_id)
        await generate_timesheet(data, call.message)
    else:
        await bot.send_message(call.message.chat.id, 'Полученные данные неверны.')
        await StatesMenu.main.set()


@logger.catch
@dp.message_handler(lambda message: message.text not in commands,
                    content_types=ContentType.TEXT, state=StatesMenu.timesheet_get_extras)
async def handle_tittle_question(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['title'] = message.text

        await message.answer(f'Имя владельца выписки было успешно обновлено.\n'
                             f'{get_message(data)}',
                             reply_markup=keyboard_handle_extracts_timesheet,
                             parse_mode=types.ParseMode.HTML)


async def generate_timesheet(data, message):
    extracts = data['extracts']
    extracts_files = []

    try:
        for extract in extracts:
            file_data = json.loads(extract['extract'])
            extract_file_id = file_data['file_id']
            extract_file_info = await bot.get_file(extract_file_id)
            extract_file_path = extract_file_info.file_path
            extract_file = await bot.download_file(extract_file_path)
            extract_file_name = file_data["file_name"].replace('.xlsx', '').replace('.xls', '')

            extracts_files.append({'extract_file': extract_file,
                                   'extract_file_name': extract_file_name,
                                   'mime': extract['mime']})

        #_document = json.loads(data['extracts'][0]['extract'])
        #file_id = _document['file_id']
        #file_info = await bot.get_file(file_id)
        #file_path = file_info.file_path
        #file = await bot.download_file(file_path)
        #file_name = _document['file_name'].replace('.xlsx', '').replace('.xls', '').replace('.csv', '')
#
        #extracts_files.append({'extract_file': file,
        #                       'extract_file_name': file_name,
        #                       'mime': data['extracts'][0]['mime']})

        result, _ = await get_timesheet_data(extracts_files, 'timesheet', title=data['title'])

        ta = TableAssembler(result)
        title = result["tittle"]
        result_tables, result_fops = ta.get_bytes()

        if result_tables:
            for result in result_tables:
                await bot.send_document(message.chat.id, types.InputFile(result, filename=f'RESULT_{title}.xls'))
        else:
            await bot.send_message(message.chat.id,
                                   'Исходя из значений данной выписки была сгенерирована пустая таблица.'
                                   'Скорее всего набор значений данной выписки является неполным или повреждённым.')

        if result_fops:
            await bot.send_document(message.chat.id, types.InputFile(result_fops, filename=f'RESULT_4ДФ_{title}.txt'))

        else:
            pass
            #await message.answer('Прикреплённый файл не является XLS-файлом')
            #logger.warning('Прикреплённый файл не является XLS-файлом')
    except NotHaveTemplate:
        await bot.send_message(message.chat.id,
                               'Не найден ни один шаблон, подходящий для обработки данной таблицы.\n'
                               'Проверьте, что алгоритм работы с подобными таблицами был добавлен.')
    except UnknownEncoding:
        await bot.send_message(message.chat.id,
                               'Мы не смогли определить кодировку вашего фала.\n'
                               'Файл повреждён или имеет неизвесную кодировку.\n'
                               'Для проверки целостности файла попробуйте открыть его в текстовом редакторе.')
    except TemplateDoesNotFit:
        await bot.send_message(message.chat.id,
                               'Ключи не подходят.\n'
                               'Скорее всего этот шаблон есть в нашей базе, но был изменен банком.\n')
    except NoColumn as ex:
        await bot.send_message(message.chat.id,
                               f'Не нашёл подходящее значение названия для столбца {ex.column_name}\n'
                               'Скорее всего в таблице нет правильного значения.\n')
    except Exception as ex:
        print(ex)
    await StatesMenu.main.set()

# TIMESHEET END


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


# BOK_PRRO
@logger.catch
@dp.message_handler(commands=['bok_prro'], state='*')
async def start_message_command(message: Message, state: FSMContext):
    #await StatesMenu.bok_prro.set()

    async with state.proxy() as data:
        data.clear()

    await StatesMenu.book_prro_get_extracts.set()
    await bot.send_message(message.chat.id, 'Ожидаю файл выписки.')


@logger.catch
def get_message(state_data: dict) -> str:
    extracts = ''

    if len(state_data['extracts']) > 0:
        extracts = ''.join([f"<b>{index + 1}: ✅{json.loads(doc['extract'])['file_name']}</b>\n" for index, doc in
                            enumerate(state_data['extracts'])])

    message = (f'Внесённое число выписок: <b>{len(state_data["extracts"])}</b>\n'
               f'Имя владельца: <b>"{state_data["title"] if "title" in state_data else "⚠️НЕТ ИМЕНИ⚠️"}"</b>:\n'
               f'Выписки: \n'
               f'{extracts}')

    return message


@logger.catch
@dp.message_handler(lambda message: message.text not in commands,
                    content_types=ContentType.TEXT, state=StatesMenu.book_prro_get_extracts)
async def handle_extract_set_title(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['title'] = message.text

        await message.answer(f'Имя владельца выписки было успешно обновлено.\n'
                             f'{get_message(data)}',
                             reply_markup=keyboard_handle_extracts,
                             parse_mode=types.ParseMode.HTML)


@logger.catch
@dp.message_handler(content_types=ContentType.DOCUMENT, state=StatesMenu.book_prro_get_extracts)
async def handle_extract(message: Message, state: FSMContext):
    document = message.document
    mime = ''

    async with state.proxy() as data:
        try:
            if hasattr(message, 'md_text'):
                data['title'] = message.md_text
        except TypeError:
            pass

        if document.mime_type in ('application/vnd.ms-excel', 'application/x-msexcel',
                                  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'):
            mime = 'xlsx'

        elif document.mime_type == 'text/csv' or document.file_name.endswith('.csv'):
            mime = 'csv'
            #if 'extracts' not in data:
            #    try:
            #        title = message.md_text
            #    except TypeError:
            #        await bot.send_message(message.chat.id, 'Данная выписка не имеет информации о владельце. '
            #                                                'Подпишите файл во время отправки.')
            #        return

        if 'extracts' in data:
            data['extracts'].append({
                'extract': document.as_json(),
                'mime': mime
            })
        else:
            data['extracts'] = [{
                'extract': document.as_json(),
                'mime': mime
            }]

        await message.answer(f'Получен файл «Выписки».\n'
                             f'{get_message(data)}',
                             reply_markup=keyboard_handle_extracts,
                             parse_mode=types.ParseMode.HTML)


@logger.catch
@dp.callback_query_handler(lambda call: call.data == "button_handle_extracts", state=StatesMenu.book_prro_get_extracts)
async def button_upload(call: CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        if "title" not in data:

            await bot.send_message(call.message.chat.id,
                                   f'⚠ <b>Обратьите внимание, что вы не указали имя владельца выписки.</b> ⚠\n'
                                   'Без указания этой информации мы не сможем правильно обработать выписки.\n'
                                   f'{get_message(data)}',
                                   reply_markup=keyboard_handle_extracts,
                                   parse_mode=types.ParseMode.HTML)
            await StatesMenu.book_prro_get_extracts.set()
            return

    await StatesMenu.bok_prro_2.set()
    await bot.edit_message_text('Ожидаю файл ПРРО', call.message.chat.id, call.message.message_id)
    #await bot.send_message(call.message.chat.id, 'Ожидаю файл ПРРО')


#@logger.catch
#@dp.message_handler(content_types=ContentType.DOCUMENT, state=StatesMenu.bok_prro)
#async def handle_extract(message: Message, state: FSMContext):
#    document = message.document
#    if document.mime_type in ('application/vnd.ms-excel', 'application/x-msexcel',
#                              'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'):
#        await message.answer('Получен файл выписки. Обрабатываем...')
#        async with state.proxy() as data:
#            data['extract'] = document.as_json()
#            data['mime'] = 'xlsx'
#
#        await StatesMenu.next()
#        await bot.send_message(message.chat.id, 'Ожидаю файл ПРРО')
#
#    elif document.mime_type == 'text/csv' or document.file_name.endswith('.csv'):
#        await StatesMenu.tittle_question_prro.set()
#        await message.answer('Получен CSV-файл. Обрабатываем...')
#        async with state.proxy() as data:
#            data['extract'] = document.as_json()
#            data['mime'] = 'csv'
#        await message.answer('Укажите имя владельца выписки.')
#    else:
#        return


#@logger.catch
#@dp.message_handler(content_types=ContentType.TEXT, state=StatesMenu.bok_prro)
#async def handle_tittle_question_prro(message: Message, state: FSMContext):
#
#    async with state.proxy() as data:
#        data['title'] = message.text
#
#    if message.text:
#        await StatesMenu.bok_prro_2.set()
#        await bot.send_message(message.chat.id, 'Ожидаю файл ПРРО')
#    else:
#        await message.answer('Полученные данные неверны.')
#        await StatesMenu.main.set()


@logger.catch
@dp.message_handler(content_types=ContentType.DOCUMENT, state=StatesMenu.bok_prro_2)
async def handle_extract(message: Message, state: FSMContext):
    try:
        prro = message.document
        if prro.mime_type in ('application/vnd.ms-excel', 'application/x-msexcel',
                              'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'):
            await message.answer('Получен файл ПРРО. Обрабатываем...')
            async with state.proxy() as data:
                extracts = data['extracts']
                extracts_files = []

                for extract in extracts:
                    file_data = json.loads(extract['extract'])
                    extract_file_id = file_data['file_id']
                    extract_file_info = await bot.get_file(extract_file_id)
                    extract_file_path = extract_file_info.file_path
                    extract_file = await bot.download_file(extract_file_path)
                    extract_file_name = message.document.file_name.replace('.xlsx', '').replace('.xls', '')

                    extracts_files.append({'extract_file': extract_file,
                                           'extract_file_name': extract_file_name,
                                           'mime': extract['mime']})

                prro_file_id = prro.file_id
                prro_file_info = await bot.get_file(prro_file_id)
                prro_file_path = prro_file_info.file_path
                prro_file = await bot.download_file(prro_file_path)

                result, rows = await get_timesheet_data(extracts_files, 'bok_prro',
                                                        title=data['title'],
                                                        prro_file=prro_file)

                data['title'] = result['tittle']

                ta = TableAssembler(result)
                result_tables, result_fops = ta.get_bytes()

                for _result in result_tables:
                    await bot.send_document(message.chat.id, types.InputFile(_result, filename=f'RESULT_{data["title"]}.xls'))

                if result_fops:
                    await bot.send_document(message.chat.id, types.InputFile(result_fops,
                                                                             filename=f'RESULT_{data["title"]}.txt'))
        else:
            await message.answer('Прикреплённый файл не является XLS-файлом')
            logger.warning('Прикреплённый файл не является XLS-файлом')

    except NotHaveTemplate:
        await bot.send_message(message.chat.id,
                               'Не найден ни один шаблон, подходящий для обработки данной таблицы.\n'
                               'Проверьте, что алгоритм работы с подобными таблицами был добавлен.')
    except UnknownEncoding:
        await bot.send_message(message.chat.id,
                               'Мы не смогли определить кодировку вашего фала.\n'
                               'Файл повреждён или имеет неизвесную кодировку.\n'
                               'Для проверки целостности файла попробуйте открыть его в текстовом редакторе.')
    except TemplateDoesNotFit:
        await bot.send_message(message.chat.id,
                               'Ключи не подходят.\n'
                               'Скорее всего этот шаблон есть в нашей базе, но был изменен банком.\n')
    except NotHaveTemplatePRRO:
        await bot.send_message(message.chat.id,
                               'Не найден ни один шаблон ПРРО, подходящий для обработки данной таблицы.\n'
                               'Проверьте, что алгоритм работы с подобными таблицами был добавлен.')

    await state.finish()
    await StatesMenu.main.set()
# END PRRO


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


@dp.message_handler(commands=['test_command'], state='*')
async def start_message_command(message: Message):
    await StatesMenu.test_state.set()
    await bot.send_message(message.chat.id, 'Генерируем пакет документов.')

    employers = Employers()

    for employer in employers.get_employers():
        if len(employer.workers) == 0:
            await bot.send_message(message.chat.id, f'❌ <b>{employer.name}</b> не имеет сотрудников.',
                                   parse_mode=types.ParseMode.HTML)
            continue
        try:
            sp = SettlementPayment(employer)
            sp_doc = sp.get_bytes()

            aowhs = AppearanceOTWHSheet(employer)
            aowhs_doc = aowhs.get_bytes()

            await send_document_group(message.chat.id, [sp_doc, aowhs_doc], employer.name)
        except NoWorkers:
            await bot.send_message(message.chat.id,
                                   f'❌ <b>{employer.name}</b> не имеет сотрудников, удовлетворяющих требованиям'
                                   f' для создания таблиц.',
                                   parse_mode=types.ParseMode.HTML)
        except WorkerNotHaveWorkHours as ex:
            await bot.send_message(message.chat.id,
                                   f'❌ У <b>{employer.name} > {ex.worker.name}</b> не проставлены часы в таблице. \n'
                                   f'К сожалению без указания этих данных я не смогу сгенерировать таблицы.\n'
                                   f'Заполните недостающие данные и попробуйте сгенерировать таблицы снова.',
                                   parse_mode=types.ParseMode.HTML)


def delete_storage():
    try:
        os.remove('./storage/storage.json')
        print(f"Storage has been successfully deleted.")
    except OSError as e:
        print(f"Error deleting the file ./storage/storage.json: {e}")


if __name__ == "__main__":
    try:
        executor.start_polling(dp, skip_updates=True)
    except Exception as ex:
        logger.critical(ex)
        delete_storage()

    input("Нажмите Enter для завершения программы...")
