import os

from aiogram import executor

import BotModule
from logger import Logger

cls_logger = Logger()
logger = cls_logger.get_logger

#storage = JSONStorage('./storage/storage.json')
#bot = Bot(token=BOT_API_TOKEN)
#dp: Dispatcher = Dispatcher(bot, storage=storage)
#
#
#def save_out():
#    dp.stop_polling()
#    asyncio.run(dp.storage.close())
#    asyncio.run(dp.storage.wait_closed())
#    return
#
#
#atexit.register(save_out)
#
#commands = ['/start',
#            '/timesheet',
#            '/extract',
#            '/extract_all',
#            '/extract_test',
#            '/bok_prro',
#            '/get_empty_book',
#            '/menu']
#
#
#@dp.message_handler(commands=['start'], state='*')
#async def start_message_command(message: Message):
#    await StatesMenu.main.set()
#    await bot.send_message(message.chat.id,
#                           'Вас приветствует бот для расчёта данных из выписок.'
#                           )
#
#
## TIMESHEET
#@dp.message_handler(commands=['timesheet'], state='*')
#async def start_message_command(message: Message, state: FSMContext):
#
#    async with state.proxy() as data:
#        data.clear()
#
#    await StatesMenu.timesheet_get_extras.set()
#    await bot.send_message(message.chat.id, 'Ожидаю файл выписки.')
#
#
#@dp.callback_query_handler(lambda call: call.data == "button_timesheet_acquiring", state=StatesMenu.main)
#async def button_upload(call: CallbackQuery):
#    await StatesMenu.timesheet_acquiring.set()
#    await bot.send_message(call.message.chat.id, 'Ожидаю файл выписки.')
#
#
#@logger.catch
#@dp.message_handler(content_types=ContentType.DOCUMENT, state=StatesMenu.timesheet_get_extras)
#async def handle_document(message: Message, state: FSMContext):
#    document = message.document
#    mime = ''
#
#    async with state.proxy() as data:
#        try:
#            if hasattr(message, 'md_text'):
#                data['title'] = message.md_text
#        except TypeError:
#            pass
#
#        if document.mime_type in ('application/vnd.ms-excel', 'application/x-msexcel',
#                                  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'):
#            mime = 'xlsx'
#
#        elif document.mime_type == 'text/csv' or document.file_name.endswith('.csv'):
#            mime = 'csv'
#
#        if 'extracts' in data:
#            data['extracts'].append({
#                'extract': document.as_json(),
#                'mime': mime
#            })
#        else:
#            data['extracts'] = [{
#                'extract': document.as_json(),
#                'mime': mime
#            }]
#
#        await message.answer(f'Получен файл «Выписки».\n'
#                             f'{get_message(data)}',
#                             reply_markup=keyboard_handle_extracts_timesheet,
#                             parse_mode=types.ParseMode.HTML)
#
#
#def find_entrepreneur(name: str, entrepreneurs: dict[str, str]) -> Union[bool, str]:
#    """
#
#    :param name: Entrepreneurs name
#    :param entrepreneurs: dict name:id
#    :return: if the entrepreneur was found, then his egrpou. if not found, return False
#    """
#    for entrepreneur, egrpou in entrepreneurs.items():
#        if name.lower() in entrepreneur.lower():
#            return f'{entrepreneur}_{egrpou}'
#
#    return False
#
#
#@logger.catch
#@dp.callback_query_handler(lambda call: call.data.startswith('fop_'), state=StatesMenu.timesheet_get_extras)
#async def pressed_button_fop(call: CallbackQuery, state: FSMContext):
#    async with state.proxy() as data:
#        _, data['title'], data['holder_id'] = call.data.split('_')
#
#    await bot.edit_message_text(f'Выписки в количестве <b>{len(data["extracts"])}шт.</b>\n'
#                                f'Имя владельца выписки: <b>{data["title"]}</b>\n'
#                                '<b>Обрабатываем...</b>',
#                                call.message.chat.id, call.message.message_id,
#                                parse_mode=types.ParseMode.HTML)
#
#    await generate_timesheet(data, call.message)
#
#
#@logger.catch
#@dp.callback_query_handler(lambda call: call.data == "button_handle_extracts_timesheet",
#                           state=StatesMenu.timesheet_get_extras)
#async def button_upload_timesheet(call: CallbackQuery, state: FSMContext):
#    entrepreneurs = Entrepreneurs()
#
#    async with state.proxy() as data:
#        if "title" not in data:
#
#            await bot.send_message(call.message.chat.id,
#                                   f'⚠ <b>Обратьите внимание, что вы не указали имя владельца выписки.</b> ⚠\n'
#                                   'Без указания этой информации мы не сможем правильно обработать выписки.\n'
#                                   'Выберите из предложенного ниже списка нужного предпринимателя.'
#                                   f'{get_message(data)}',
#                                   #reply_markup=keyboard_handle_extracts_timesheet,
#                                   reply_markup=entrepreneurs_menu(entrepreneurs),
#                                   parse_mode=types.ParseMode.HTML)
#            return
#
#        entrepreneur: bool | str = find_entrepreneur(data['title'], entrepreneurs)
#
#        if not entrepreneur:
#            await bot.send_message(call.message.chat.id,
#                                   f'⚠ <b>Мы не смогли найти владельца выписки!</b> ⚠\n'
#                                   'Без указания этой информации мы не сможем правильно обработать выписки.\n'
#                                   'Выберите из предложенного ниже списка нужного предпринимателя.'
#                                   f'{get_message(data)}',
#                                   # reply_markup=keyboard_handle_extracts_timesheet,
#                                   reply_markup=entrepreneurs_menu(entrepreneurs),
#                                   parse_mode=types.ParseMode.HTML)
#            return
#
#        data['title'], data['holder_id'] = entrepreneur.split('_')
#
#        if 'extracts' in data and data['extracts']:
#            await bot.edit_message_text(f'Выписки в количестве <b>{len(data["extracts"])}шт.</b>\n'
#                                        f'Имя владельца выписки: <b>{data["title"]}</b>\n'
#                                        '<b>Обрабатываем...</b>',
#                                        call.message.chat.id, call.message.message_id,
#                                        parse_mode=types.ParseMode.HTML)
#            await generate_timesheet(data, call.message)
#        else:
#            await bot.send_message(call.message.chat.id, 'Полученные данные неверны.')
#            await StatesMenu.main.set()
#
#
#@logger.catch
#@dp.message_handler(lambda message: message.text not in commands,
#                    content_types=ContentType.TEXT, state=StatesMenu.timesheet_get_extras)
#async def handle_tittle_question(message: Message, state: FSMContext):
#    entrepreneurs = Entrepreneurs()
#
#    async with state.proxy() as data:
#        data['title'] = message.text
#
#        entrepreneur: bool | str = find_entrepreneur(data['title'], entrepreneurs)
#        if not entrepreneur:
#            await bot.send_message(message.chat.id,
#                                   f'⚠ <b>Мы не смогли найти указанного владельца выписки!</b> ⚠\n'
#                                   'Без указания этой информации мы не сможем правильно обработать выписки.\n'
#                                   'Выберите из предложенного ниже списка нужного предпринимателя.'
#                                   f'{get_message(data)}',
#                                   # reply_markup=keyboard_handle_extracts_timesheet,
#                                   reply_markup=entrepreneurs_menu(entrepreneurs),
#                                   parse_mode=types.ParseMode.HTML)
#            return
#
#        data['title'], data['holder_id'] = entrepreneur.split('_')
#
#        await message.answer(f'Имя владельца выписки было успешно обновлено.\n'
#                             f'{get_message(data)}',
#                             reply_markup=keyboard_handle_extracts_timesheet,
#                             parse_mode=types.ParseMode.HTML)
#
#
#async def generate_timesheet(data, message):
#    extracts = data['extracts']
#    extracts_files = []
#
#    try:
#        for extract in extracts:
#            file_data = json.loads(extract['extract'])
#            extract_file_id = file_data['file_id']
#            extract_file_info = await bot.get_file(extract_file_id)
#            extract_file_path = extract_file_info.file_path
#            extract_file = await bot.download_file(extract_file_path)
#            extract_file_name = file_data["file_name"].replace('.xlsx', '').replace('.xls', '')
#
#            extracts_files.append({'extract_file': extract_file,
#                                   'extract_file_name': extract_file_name,
#                                   'mime': extract['mime']})
#
#        #_document = json.loads(data['extracts'][0]['extract'])
#        #file_id = _document['file_id']
#        #file_info = await bot.get_file(file_id)
#        #file_path = file_info.file_path
#        #file = await bot.download_file(file_path)
#        #file_name = _document['file_name'].replace('.xlsx', '').replace('.xls', '').replace('.csv', '')
##
#        #extracts_files.append({'extract_file': file,
#        #                       'extract_file_name': file_name,
#        #                       'mime': data['extracts'][0]['mime']})
#
#        result, _, timerange = await get_timesheet_data(extracts_files, 'timesheet',
#                                                        title=data['title'], holder_id=data['holder_id'])
#
#        ta = TableAssembler(result, timerange=timerange)
#        result_tables, result_fops = ta.get_bytes()
#
#        if result_tables:
#            for result in result_tables:
#                await bot.send_document(message.chat.id,
#                                        types.InputFile(result["workbooks_bytes"],
#                                                        filename=f'Книга за {result["workbooks_month"]}_'
#                                                                 f'{data["title"]}.xls'))
#        else:
#            await bot.send_message(message.chat.id,
#                                   'Исходя из значений данной выписки была сгенерирована пустая таблица.'
#                                   'Скорее всего набор значений данной выписки является неполным или повреждённым.')
#
#        if result_fops:
#            await bot.send_document(message.chat.id, types.InputFile(result_fops,
#                                                                     filename=f'4Дф_{data["title"]}.txt'))
#
#        else:
#            pass
#            #await message.answer('Прикреплённый файл не является XLS-файлом')
#            #logger.warning('Прикреплённый файл не является XLS-файлом')
#    except NotHaveTemplate:
#        await bot.send_message(message.chat.id,
#                               'Не найден ни один шаблон, подходящий для обработки данной таблицы.\n'
#                               'Проверьте, что алгоритм работы с подобными таблицами был добавлен.')
#    except UnknownEncoding:
#        await bot.send_message(message.chat.id,
#                               'Мы не смогли определить кодировку вашего фала.\n'
#                               'Файл повреждён или имеет неизвесную кодировку.\n'
#                               'Для проверки целостности файла попробуйте открыть его в текстовом редакторе.')
#    except TemplateDoesNotFit:
#        await bot.send_message(message.chat.id,
#                               'Ключи не подходят.\n'
#                               'Скорее всего этот шаблон есть в нашей базе, но был изменен банком.\n')
#    except NoColumn as ex:
#        await bot.send_message(message.chat.id,
#                               f'Не нашёл подходящее значение названия для столбца {ex.column_name}\n'
#                               'Скорее всего в таблице нет правильного значения.\n')
#    except Exception as ex:
#        print(ex)
#    await StatesMenu.main.set()
#
## TIMESHEET END
#
#
#@dp.message_handler(commands=['extract'], state='*')
#async def start_message_command(message: Message):
#    await StatesMenu.extract.set()
#    await bot.send_message(message.chat.id, 'Ожидаю файл выписки.')
#
#
#@dp.callback_query_handler(lambda call: call.data == "button_extract", state=StatesMenu.main)
#async def button_upload(call: CallbackQuery):
#    await StatesMenu.extract.set()
#    await bot.send_message(call.message.chat.id, 'Ожидаю файл выписки.')
#
#
#@logger.catch
#@dp.message_handler(content_types=ContentType.DOCUMENT, state=StatesMenu.extract)
#async def handle_document(message: Message):
#    document = message.document
#    if document.mime_type in ('application/vnd.ms-excel', 'application/x-msexcel',
#                              'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'):
#        await message.answer('Получен XLS-файл. Обрабатываем...')
#        file_id = document.file_id
#        file_info = await bot.get_file(file_id)
#        file_path = file_info.file_path
#        file = await bot.download_file(file_path)
#        file_name = message.document.file_name.replace('.xlsx', '').replace('.xls', '')
#        result, rows = await get_timesheet_data(file, file_name, 'extract')
#
#        rows_io = io.BytesIO()
#        rows_io.write(rows.encode('utf-8'))
#        rows_io.seek(0)
#
#        msg = f'Всего: <code>{result["revenue"] if result.get("revenue") else "0.00"}</code>\n' \
#              f'1 Квартал: <code>{result["quarter_1"] if result.get("quarter_1") else "0.00"}</code>\n' \
#              f'2 Квартал: <code>{result["quarter_2"] if result.get("quarter_2") else "0.00"}</code>\n' \
#              f'3 Квартал: <code>{result["quarter_3"] if result.get("quarter_3") else "0.00"}</code>\n' \
#              f'4 Квартал: <code>{result["quarter_4"] if result.get("quarter_4") else "0.00"}</code>\n'
#
#        await bot.send_message(message.chat.id,
#                               msg,
#                               parse_mode=ParseMode.HTML)
#
#    else:
#        await message.answer('Прикреплённый файл не является XLS-файлом')
#        logger.warning('Прикреплённый файл не является XLS-файлом')
#
#    await StatesMenu.main.set()
#
#
#@dp.message_handler(commands=['extract_all'], state='*')
#async def start_message_command(message: Message):
#    await StatesMenu.extract_all.set()
#    await bot.send_message(message.chat.id, 'Ожидаю файл выписки.')
#
#
#@logger.catch
#@dp.message_handler(content_types=ContentType.DOCUMENT, state=StatesMenu.extract_all)
#async def handle_document(message: Message):
#    document = message.document
#    if document.mime_type in ('application/vnd.ms-excel', 'application/x-msexcel',
#                              'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'):
#        await message.answer('Получен XLS-файл. Обрабатываем...')
#        file_id = document.file_id
#        file_info = await bot.get_file(file_id)
#        file_path = file_info.file_path
#        file = await bot.download_file(file_path)
#        result = get_result(file)
#
#        await bot.send_message(message.chat.id,
#                               f'Всего: <code>{result["positives"] if result.get("positives") else "0.00"}</code>\n'
#                               f'Затраты: <code>{result["negatives"] if result.get("negatives") else "0.00"}</code>',
#                               parse_mode=ParseMode.HTML)
#
#    else:
#        await message.answer('Прикреплённый файл не является XLS-файлом')
#        logger.warning('Прикреплённый файл не является XLS-файлом')
#
#    await StatesMenu.main.set()
#
#
#@dp.message_handler(commands=['extract_test'], state='*')
#async def start_message_command(message: Message):
#    await StatesMenu.extract_test.set()
#    await bot.send_message(message.chat.id, 'Ожидаю файл выписки.')
#
#
#@logger.catch
#@dp.message_handler(content_types=ContentType.DOCUMENT, state=StatesMenu.extract_test)
#async def handle_document(message: Message):
#    document = message.document
#    if document.mime_type in ('application/vnd.ms-excel', 'application/x-msexcel',
#                              'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'):
#        await message.answer('Получен XLS-файл. Обрабатываем...')
#        file_id = document.file_id
#        file_info = await bot.get_file(file_id)
#        file_path = file_info.file_path
#        file = await bot.download_file(file_path)
#        file_name = message.document.file_name.replace('.xlsx', '').replace('.xls', '')
#        result, rows, timerange = await get_timesheet_data(file, file_name, 'extract')
#
#        rows_io = io.BytesIO()
#        rows_io.write(rows.encode('utf-8'))
#        rows_io.seek(0)
#
#        msg = f'Всего: <code>{result["revenue"] if result.get("revenue") else "0.00"}</code>\n' \
#              f'1 Квартал: <code>{result["quarter_1"] if result.get("quarter_1") else "0.00"}</code>\n' \
#              f'2 Квартал: <code>{result["quarter_2"] if result.get("quarter_2") else "0.00"}</code>\n' \
#              f'3 Квартал: <code>{result["quarter_3"] if result.get("quarter_3") else "0.00"}</code>\n' \
#              f'4 Квартал: <code>{result["quarter_4"] if result.get("quarter_4") else "0.00"}</code>\n'
#
#        await bot.send_message(message.chat.id,
#                               msg,
#                               parse_mode=ParseMode.HTML)
#        await bot.send_document(message.chat.id,
#                                types.InputFile(rows_io, filename='RESULT.txt'))
#
#    else:
#        await message.answer('Прикреплённый файл не является XLS-файлом')
#        logger.warning('Прикреплённый файл не является XLS-файлом')
#
#    await StatesMenu.main.set()
#
#
## BOK_PRRO
#@logger.catch
#@dp.message_handler(commands=['bok_prro'], state='*')
#async def start_message_command(message: Message, state: FSMContext):
#    #await StatesMenu.bok_prro.set()
#
#    async with state.proxy() as data:
#        data.clear()
#
#    await StatesMenu.book_prro_get_extracts.set()
#    await bot.send_message(message.chat.id, 'Ожидаю файл выписки.')
#
#
#@logger.catch
#def get_message(state_data: dict) -> str:
#    extracts = ''
#
#    if len(state_data['extracts']) > 0:
#        extracts = ''.join([f"<b>{index + 1}: ✅{json.loads(doc['extract'])['file_name']}</b>\n" for index, doc in
#                            enumerate(state_data['extracts'])])
#
#    message = (f'Внесённое число выписок: <b>{len(state_data["extracts"])}</b>\n'
#               f'Имя владельца: <b>"{state_data["title"] if "title" in state_data else "⚠️НЕТ ИМЕНИ⚠️"}"</b>:\n'
#               f'Выписки: \n'
#               f'{extracts}')
#
#    return message
#
#
#@logger.catch
#@dp.message_handler(lambda message: message.text not in commands,
#                    content_types=ContentType.TEXT, state=StatesMenu.book_prro_get_extracts)
#async def handle_extract_set_title(message: Message, state: FSMContext):
#    async with state.proxy() as data:
#        data['title'] = message.text
#
#        await message.answer(f'Имя владельца выписки было успешно обновлено.\n'
#                             f'{get_message(data)}',
#                             reply_markup=keyboard_handle_extracts,
#                             parse_mode=types.ParseMode.HTML)
#
#
#@logger.catch
#@dp.message_handler(content_types=ContentType.DOCUMENT, state=StatesMenu.book_prro_get_extracts)
#async def handle_extract(message: Message, state: FSMContext):
#    document = message.document
#    mime = ''
#
#    async with state.proxy() as data:
#        try:
#            if hasattr(message, 'md_text'):
#                data['title'] = message.md_text
#        except TypeError:
#            pass
#
#        if document.mime_type in ('application/vnd.ms-excel', 'application/x-msexcel',
#                                  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'):
#            mime = 'xlsx'
#
#        elif document.mime_type == 'text/csv' or document.file_name.endswith('.csv'):
#            mime = 'csv'
#            #if 'extracts' not in data:
#            #    try:
#            #        title = message.md_text
#            #    except TypeError:
#            #        await bot.send_message(message.chat.id, 'Данная выписка не имеет информации о владельце. '
#            #                                                'Подпишите файл во время отправки.')
#            #        return
#
#        if 'extracts' in data:
#            data['extracts'].append({
#                'extract': document.as_json(),
#                'mime': mime
#            })
#        else:
#            data['extracts'] = [{
#                'extract': document.as_json(),
#                'mime': mime
#            }]
#
#        await message.answer(f'Получен файл «Выписки».\n'
#                             f'{get_message(data)}',
#                             reply_markup=keyboard_handle_extracts,
#                             parse_mode=types.ParseMode.HTML)
#
#
#
#
#
#@logger.catch
#@dp.callback_query_handler(lambda call: call.data == "button_handle_extracts", state=StatesMenu.book_prro_get_extracts)
#async def button_upload(call: CallbackQuery, state: FSMContext):
#    entrepreneurs = Entrepreneurs()
#
#    async with state.proxy() as data:
#        if "title" not in data:
#
#            await bot.send_message(call.message.chat.id,
#                                   f'⚠ <b>Обратите внимание, что вы не указали имя владельца выписки.</b> ⚠\n'
#                                   'Без указания этой информации мы не сможем правильно обработать выписки.\n'
#                                   'Выберите из списка предприниателей представленного ниже.'
#                                   f'{get_message(data)}',
#                                   reply_markup=entrepreneurs_menu(entrepreneurs),
#                                   parse_mode=types.ParseMode.HTML)
#            await StatesMenu.book_prro_get_extracts.set()
#            return
#
#        entrepreneur: bool | str = find_entrepreneur(data['title'], entrepreneurs)
#
#        if not entrepreneur:
#            await bot.send_message(call.message.chat.id,
#                                   f'⚠ <b>Мы не смогли найти владельца выписки!</b> ⚠\n'
#                                   'Без указания этой информации мы не сможем правильно обработать выписки.\n'
#                                   'Выберите из предложенного ниже списка нужного предпринимателя.'
#                                   f'{get_message(data)}',
#                                   # reply_markup=keyboard_handle_extracts_timesheet,
#                                   reply_markup=entrepreneurs_menu(entrepreneurs),
#                                   parse_mode=types.ParseMode.HTML)
#            return
#
#        data['title'], data['holder_id'] = entrepreneur.split('_')
#
#    await StatesMenu.bok_prro_2.set()
#    await bot.edit_message_text('Ожидаю файл ПРРО', call.message.chat.id, call.message.message_id)
#    #await bot.send_message(call.message.chat.id, 'Ожидаю файл ПРРО')
#
#
##@logger.catch
##@dp.message_handler(content_types=ContentType.DOCUMENT, state=StatesMenu.bok_prro)
##async def handle_extract(message: Message, state: FSMContext):
##    document = message.document
##    if document.mime_type in ('application/vnd.ms-excel', 'application/x-msexcel',
##                              'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'):
##        await message.answer('Получен файл выписки. Обрабатываем...')
##        async with state.proxy() as data:
##            data['extract'] = document.as_json()
##            data['mime'] = 'xlsx'
##
##        await StatesMenu.next()
##        await bot.send_message(message.chat.id, 'Ожидаю файл ПРРО')
##
##    elif document.mime_type == 'text/csv' or document.file_name.endswith('.csv'):
##        await StatesMenu.tittle_question_prro.set()
##        await message.answer('Получен CSV-файл. Обрабатываем...')
##        async with state.proxy() as data:
##            data['extract'] = document.as_json()
##            data['mime'] = 'csv'
##        await message.answer('Укажите имя владельца выписки.')
##    else:
##        return
#
#
##@logger.catch
##@dp.message_handler(content_types=ContentType.TEXT, state=StatesMenu.bok_prro)
##async def handle_tittle_question_prro(message: Message, state: FSMContext):
##
##    async with state.proxy() as data:
##        data['title'] = message.text
##
##    if message.text:
##        await StatesMenu.bok_prro_2.set()
##        await bot.send_message(message.chat.id, 'Ожидаю файл ПРРО')
##    else:
##        await message.answer('Полученные данные неверны.')
##        await StatesMenu.main.set()
#
#
#@logger.catch
#@dp.message_handler(content_types=ContentType.DOCUMENT, state=StatesMenu.bok_prro_2)
#async def handle_extract(message: Message, state: FSMContext):
#    try:
#        prro = message.document
#        prro_mime = ''
#        if prro.mime_type in ('application/vnd.ms-excel', 'application/x-msexcel',
#                              'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'):
#            prro_mime = 'xlsx'
#        elif prro.mime_type == 'text/csv' or prro.file_name.endswith('.csv'):
#            prro_mime = 'csv'
#        else:
#            await message.answer('Прикреплённый файл РРО имеет не поддерживаемый тип.')
#            logger.warning('Прикреплённый файл не является XLS-файлом')
#
#        await message.answer('Получен файл ПРРО. Обрабатываем...')
#        async with state.proxy() as data:
#            extracts = data['extracts']
#            extracts_files = []
#
#            for extract in extracts:
#                file_data = json.loads(extract['extract'])
#                extract_file_id = file_data['file_id']
#                extract_file_info = await bot.get_file(extract_file_id)
#                extract_file_path = extract_file_info.file_path
#                extract_file = await bot.download_file(extract_file_path)
#                extract_file_name = message.document.file_name.replace('.xlsx', '').replace('.xls', '')
#
#                extracts_files.append({'extract_file': extract_file,
#                                       'extract_file_name': extract_file_name,
#                                       'mime': extract['mime']})
#
#            prro_file_id = prro.file_id
#            prro_file_info = await bot.get_file(prro_file_id)
#            prro_file_path = prro_file_info.file_path
#            prro_file = await bot.download_file(prro_file_path)
#
#            result, rows, timerange = await get_timesheet_data(extracts_files, 'bok_prro',
#                                                               title=data['title'],
#                                                               holder_id=data['holder_id'],
#                                                               prro_file=prro_file,
#                                                               prro_mime=prro_mime)
#
#            data['title'] = result['tittle']
#
#            ta = TableAssembler(result, timerange=timerange)
#            result_tables, result_fops = ta.get_bytes()
#
#            for _result in result_tables:
#                await bot.send_document(message.chat.id,
#                                        types.InputFile(_result["workbooks_bytes"],
#                                                        filename=f'Книга за {_result["workbooks_month"]}_'
#                                                                 f'{data["title"]}.xls'))
#
#            if result_fops:
#                await bot.send_document(message.chat.id, types.InputFile(result_fops,
#                                                                         filename=f'4Дф {data["title"]}.txt'))
#
#    except NotHaveTemplate:
#        await bot.send_message(message.chat.id,
#                               'Не найден ни один шаблон, подходящий для обработки данной таблицы.\n'
#                               'Проверьте, что алгоритм работы с подобными таблицами был добавлен.')
#    except UnknownEncoding:
#        await bot.send_message(message.chat.id,
#                               'Мы не смогли определить кодировку вашего фала.\n'
#                               'Файл повреждён или имеет неизвесную кодировку.\n'
#                               'Для проверки целостности файла попробуйте открыть его в текстовом редакторе.')
#    except TemplateDoesNotFit:
#        await bot.send_message(message.chat.id,
#                               'Ключи не подходят.\n'
#                               'Скорее всего этот шаблон есть в нашей базе, но был изменен банком.\n')
#    except NotHaveTemplatePRRO:
#        await bot.send_message(message.chat.id,
#                               'Не найден ни один шаблон ПРРО, подходящий для обработки данной таблицы.\n'
#                               'Проверьте, что алгоритм работы с подобными таблицами был добавлен.')
#
#    await state.finish()
#    await StatesMenu.main.set()
## END PRRO
#
#
## EMPTY BOOK
#@logger.catch
#@dp.message_handler(commands=['get_empty_book'], state='*')
#async def empty_book_command(message: Message, state: FSMContext):
#    #await StatesMenu.bok_prro.set()
#
#    async with state.proxy() as data:
#        data.clear()
#
#    await StatesMenu.empty_book_change_month.set()
#    await bot.send_message(message.chat.id, 'Выберите месяц:', reply_markup=month_keyboard)
#
#
#@logger.catch
#@dp.callback_query_handler(lambda call: call.data.startswith("month_"), state=StatesMenu.empty_book_change_month)
#async def set_name(call: CallbackQuery, state: FSMContext):
#    async with state.proxy() as data:
#        data['month'] = call.data.replace('month_', '')
#
#    await StatesMenu.change_name.set()
#    await bot.send_message(call.message.chat.id, 'Укажите имя владельца выписки:')
#
#
#@logger.catch
#@dp.message_handler(lambda message: message.text not in commands,
#                    content_types=ContentType.TEXT, state=StatesMenu.change_name)
#async def generate_empty_extract(message: Message, state: FSMContext):
#    title = message.text
#    async with state.proxy() as data:
#        month = data['month']
#
#    ta = TableAssembler(_tittle=title, _month=month)
#    result_tables, _ = ta.get_bytes()
#
#    for _result in result_tables:
#        await bot.send_document(message.chat.id,
#                                types.InputFile(_result["workbooks_bytes"],
#                                                filename=f'Книга за {_result["workbooks_month"]}_'
#                                                         f'{data["title"]}.xls'))
#
## END EMPTY BOOK
#
#
## MENU
#@dp.message_handler(commands=['menu'], state='*')
#async def change_entrepreneurs_command(message: Message):
#    try:
#        entrepreneurs = DBClient().get_list_entrepreneurs()
#
#        if not entrepreneurs:
#            await bot.send_message(message.chat.id,
#                                   f'Для отображения этого меню вам нужно добавить хотя бы одну выписку, '
#                                   f'для хотя бы одного предпринимателя.')
#            return
#
#        await EntrepreneursMenu.change_entrepreneur.set()
#        await bot.send_message(message.chat.id,
#                               f'Выберите предпринимателя из списка предложенного ниже.',
#                               reply_markup=entrepreneurs_keyboard(entrepreneurs))
#    except Exception as ex:
#        logger.exception(ex)
#        await bot.send_message(message.chat.id,
#                               f'К сожалению меню на данный момент недоступно.')
#
#
#@logger.catch
#@dp.callback_query_handler(lambda call: call.data.startswith('fop_'), state=EntrepreneursMenu.change_entrepreneur)
#async def changed_entrepreneur(call: CallbackQuery, state: FSMContext):
#    try:
#        async with state.proxy() as data:
#            _, data['title'], data['holder_id'] = call.data.split('_')
#
#        extracts = DBClient().get_list_extracts(data['holder_id'])
#
#        if not extracts:
#            entrepreneurs = DBClient().get_list_entrepreneurs()
#            await bot.edit_message_text(f'Для указанного предпринимателя нет ни одной выписки.\n'
#                                        f'Выберите предпринимателя из списка предложенного ниже.',
#                                        call.message.chat.id, call.message.message_id,
#                                        reply_markup=entrepreneurs_keyboard(entrepreneurs))
#            return
#
#        await EntrepreneursMenu.extracts_menu.set()
#        await bot.edit_message_text(f'Предприниматель <b>{data["title"]}</b> имеет'
#                                    f'выписки в количестве <b>{len(extracts)}шт.</b>'
#                                    'Выберите любую выписку из предложенных для просмотра деталей.',
#                                    call.message.chat.id, call.message.message_id,
#                                    reply_markup=extracts_keyboard(extracts),
#                                    parse_mode=types.ParseMode.HTML)
#    except Exception as ex:
#        logger.exception(ex)
#        await bot.edit_message_text(f'К сожалению не удалось получить список выписок для данного предпринимателя.',
#                                    call.message.chat.id, call.message.message_id)
#
#
#@logger.catch
#@dp.callback_query_handler(lambda call: call.data.startswith('ex_'), state=EntrepreneursMenu.extracts_menu)
#async def changed_extract(call: CallbackQuery, state: FSMContext):
#    try:
#        async with state.proxy() as data:
#            await EntrepreneursMenu.extract_detail.set()
#            data['extract_hash'] = call.data.replace('ex_', "")
#
#            details = DBClient().extract_details(data['extract_hash'], data['holder_id'])
#            extract_name = DBClient().get_extract_name(data['extract_hash'], data['holder_id'])
#            timerange = DBClient().get_extract_timerange(data['extract_hash'], data['holder_id'])
#
#            await EntrepreneursMenu.extract_detail.set()
#            await bot.edit_message_text(f'Предприниматель: <b>{data["title"]}</b>\n'
#                                        f'Название выписки: <b>{extract_name}</b>\n'
#                                        f'Количество транзакций: <b>{details["transactions_count"]}.шт</b>\n'
#                                        f'Период: <b>{timerange}</b>',
#                                        call.message.chat.id, call.message.message_id,
#                                        reply_markup=extract_details_keyboard(data['extract_hash']),
#                                        parse_mode=types.ParseMode.HTML)
#    except Exception as ex:
#        logger.exception(ex)
#        await bot.edit_message_text(f'Не удалось получить детализацию по выписке.',
#                                    call.message.chat.id, call.message.message_id)
#
#
#@logger.catch
#@dp.callback_query_handler(lambda call: call.data.startswith('delete_extract_'), state=EntrepreneursMenu.extract_detail)
#async def del_extract(call: CallbackQuery, state: FSMContext):
#    extract_hash = call.data.replace('delete_extract_', '')
#    await EntrepreneursMenu.extract_detail.set()
#    async with state.proxy() as data:
#        holder_id = data['holder_id']
#        extract_name = DBClient().get_extract_name(extract_hash, data['holder_id'])
#
#    try:
#        rows_deleted = DBClient().delete_extract(extract_name, holder_id)
#        extracts = DBClient().get_list_extracts(holder_id)
#        await bot.edit_message_text(f'Выписка <b>{extract_name}</b> была успешно удалена.\n'
#                                    f'Всего удалено <b>{rows_deleted}</b> записей.',
#                                    call.message.chat.id, call.message.message_id,
#                                    reply_markup=extracts_keyboard(extracts),
#                                    parse_mode=types.ParseMode.HTML)
#        return
#
#    except Exception as ex:
#        logger.exception(ex)
#        details = DBClient().extract_details(data['extract_name'], data['holder_id'])
#        await bot.edit_message_text(f'Не удалось удалить: <b>{extract_name}</b>\n',
#                                    f'Предприниматель: <b>{data["title"]}</b>\n'
#                                    f'Название выписки: <b>{data["extract_name"]}шт.</b>'
#                                    f'Количество транзакций: <b>{details["transactions_count"]}</b>'
#                                    f'Период: <b>с по</b>',
#                                    call.message.chat.id, call.message.message_id,
#                                    reply_markup=extract_details_keyboard(data['extract_name']),
#                                    parse_mode=types.ParseMode.HTML)
#
#
#@logger.catch
#@dp.callback_query_handler(lambda call: call.data.startswith('back_extracts_'), state=EntrepreneursMenu.extract_detail)
#async def pressed_back_button(call: CallbackQuery):
#    await change_entrepreneurs_command(call.message)
#
#
## END MENU
#
#async def send_document_group(chat_id, documents, title: str):
#    media = []
#    for num, document_data in enumerate(documents):
#        message = ''
#        file_name = f'Табель 7 {title}.xlsx'
#        if num == 0:
#            message = f'{title}'
#            file_name = f'Расчётно-платёжная {title}.xlsx'
#
#        media.append(types.InputMediaDocument(media=types.InputFile(document_data, filename=file_name), caption=message))
#
#    await bot.send_media_group(chat_id=chat_id, media=media)
#
#
#@dp.message_handler(commands=['test_command'], state='*')
#async def start_message_command(message: Message):
#    await StatesMenu.test_state.set()
#    await bot.send_message(message.chat.id, 'Генерируем пакет документов.')
#
#    employers = Employers()
#
#    for employer in employers.get_employers():
#        if len(employer.workers) == 0:
#            await bot.send_message(message.chat.id, f'❌ <b>{employer.name}</b> не имеет сотрудников.',
#                                   parse_mode=types.ParseMode.HTML)
#            continue
#        try:
#            sp = SettlementPayment(employer)
#            sp_doc = sp.get_bytes()
#
#            aowhs = AppearanceOTWHSheet(employer)
#            aowhs_doc = aowhs.get_bytes()
#
#            await send_document_group(message.chat.id, [sp_doc, aowhs_doc], employer.name)
#        except NoWorkers:
#            await bot.send_message(message.chat.id,
#                                   f'❌ <b>{employer.name}</b> не имеет сотрудников, удовлетворяющих требованиям'
#                                   f' для создания таблиц.',
#                                   parse_mode=types.ParseMode.HTML)
#        except WorkerNotHaveWorkHours as ex:
#            await bot.send_message(message.chat.id,
#                                   f'❌ У <b>{employer.name} > {ex.worker.name}</b> не проставлены часы в таблице. \n'
#                                   f'К сожалению без указания этих данных я не смогу сгенерировать таблицы.\n'
#                                   f'Заполните недостающие данные и попробуйте сгенерировать таблицы снова.',
#                                   parse_mode=types.ParseMode.HTML)


def delete_storage():
    try:
        os.remove('./storage/storage.json')
        print(f"Storage has been successfully deleted.")
    except OSError as e:
        print(f"Error deleting the file ./storage/storage.json: {e}")


if __name__ == "__main__":
    try:
        executor.start_polling(BotModule.dp, skip_updates=True)
    except Exception as ex:
        logger.critical(ex)
        delete_storage()

    input("Нажмите Enter для завершения программы...")
