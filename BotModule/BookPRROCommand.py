import json

from aiogram.dispatcher import FSMContext
from aiogram.types import Message, ContentType, ParseMode, CallbackQuery, InputFile

from BotModule import logger, dp, bot, commands
from BotModule.Common import get_message, find_entrepreneur, get_missing_months, get_message_prro
from BotModule.Keyboards import keyboard_handle_extracts, entrepreneurs_menu, button_handle_prro, keyboard_handle_prro
from BotModule.States import StatesMenu
from Exceptions import NotHaveTemplate, UnknownEncoding, TemplateDoesNotFit, NotHaveTemplatePRRO
from XLAssembler import TableAssembler
from calculating import get_timesheet_data
from cloud_sheets import Entrepreneurs


@logger.catch
@dp.message_handler(commands=['bok_prro'], state='*')
async def start_message_command(message: Message, state: FSMContext):

    async with state.proxy() as data:
        data.clear()

    await StatesMenu.book_prro_get_extracts.set()
    await bot.send_message(message.chat.id, 'Ожидаю файл выписки.')


@logger.catch
@dp.message_handler(lambda message: message.text not in commands,
                    content_types=ContentType.TEXT, state=StatesMenu.book_prro_get_extracts)
async def handle_extract_set_title(message: Message, state: FSMContext):
    entrepreneurs = Entrepreneurs()

    async with state.proxy() as data:
        data['title'] = message.text

        entrepreneur: bool | str = find_entrepreneur(data['title'], entrepreneurs)
        if not entrepreneur:
            await bot.send_message(message.chat.id,
                                   f'⚠ <b>Мы не смогли найти указанного владельца выписки!</b> ⚠\n'
                                   'Без указания этой информации мы не сможем правильно обработать выписки.\n'
                                   'Выберите из предложенного ниже списка нужного предпринимателя.'
                                   f'{get_message(data)}',
                                   reply_markup=entrepreneurs_menu(entrepreneurs),
                                   parse_mode=ParseMode.HTML)
            return

        data['title'], data['holder_id'] = entrepreneur.split('_')
    async with state.proxy() as data:
        data['title'] = message.text

        await message.answer(f'Имя владельца выписки было успешно обновлено.\n'
                             f'{get_message(data)}',
                             reply_markup=keyboard_handle_extracts,
                             parse_mode=ParseMode.HTML)


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
                             parse_mode=ParseMode.HTML)


@logger.catch
@dp.callback_query_handler(lambda call: call.data.startswith('fop_'), state=StatesMenu.book_prro_get_extracts)
async def pressed_button_fop(call: CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        _, data['title'], data['holder_id'] = call.data.split('_')

    await StatesMenu.bok_prro_2.set()
    await bot.edit_message_text('Ожидаю файл ПРРО', call.message.chat.id, call.message.message_id)


@logger.catch
@dp.callback_query_handler(lambda call: call.data == "button_handle_extracts", state=StatesMenu.book_prro_get_extracts)
async def button_upload(call: CallbackQuery, state: FSMContext):
    entrepreneurs = Entrepreneurs()

    async with state.proxy() as data:
        if "title" not in data:

            await bot.send_message(call.message.chat.id,
                                   f'⚠ <b>Обратите внимание, что вы не указали имя владельца выписки.</b> ⚠\n'
                                   'Без указания этой информации мы не сможем правильно обработать выписки.\n'
                                   'Выберите из списка предприниателей представленного ниже.'
                                   f'{get_message(data)}',
                                   reply_markup=entrepreneurs_menu(entrepreneurs),
                                   parse_mode=ParseMode.HTML)
            await StatesMenu.book_prro_get_extracts.set()
            return

        entrepreneur: bool | str = find_entrepreneur(data['title'], entrepreneurs)

        if not entrepreneur:
            await bot.send_message(call.message.chat.id,
                                   f'⚠ <b>Мы не смогли найти владельца выписки!</b> ⚠\n'
                                   'Без указания этой информации мы не сможем правильно обработать выписки.\n'
                                   'Выберите из предложенного ниже списка нужного предпринимателя.'
                                   f'{get_message(data)}',
                                   reply_markup=entrepreneurs_menu(entrepreneurs),
                                   parse_mode=ParseMode.HTML)
            return

        data['title'], data['holder_id'] = entrepreneur.split('_')

    await StatesMenu.bok_prro_2.set()
    await bot.edit_message_text('Ожидаю файл ПРРО', call.message.chat.id, call.message.message_id)


@logger.catch
@dp.message_handler(content_types=ContentType.DOCUMENT, state=StatesMenu.bok_prro_2)
async def handle_prro(message: Message, state: FSMContext):
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
        else:
            await message.answer('Прикреплённый файл РРО имеет не поддерживаемый тип.')
            logger.warning('Прикреплённый файл не является XLS-файлом')

        if 'prro' in data:
            data['prro'].append({
                'file_data': document.as_json(),
                'mime': mime
            })
        else:
            data['prro'] = [{
                'file_data': document.as_json(),
                'mime': mime
            }]

        await message.answer(f'Получен файл «ПРРО».\n'
                             f'{get_message_prro(data)}',
                             reply_markup=keyboard_handle_prro,
                             parse_mode=ParseMode.HTML)


@logger.catch
@dp.callback_query_handler(lambda call: call.data == "button_handle_prro", state=StatesMenu.bok_prro_2)
async def button_prro_upload(call: CallbackQuery, state: FSMContext):
    await handle_extract(call.message, state)


async def handle_extract(message: Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            extracts = data['extracts']
            extracts_files = []

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

            prro_files = []

            for prro in data['prro']:
                mime = prro['mime']
                prro = json.loads(prro['file_data'])
                prro_file_id = prro['file_id']
                prro_name = prro['file_name']
                prro_file_info = await bot.get_file(prro_file_id)
                prro_file_path = prro_file_info.file_path
                prro_file = await bot.download_file(prro_file_path)

                prro_files.append([prro_name, prro_file, mime])

            result, rows, timerange, lost_months = await get_timesheet_data(extracts_files, 'bok_prro',
                                                                            title=data['title'],
                                                                            holder_id=data['holder_id'],
                                                                            prro_files=prro_files)

            data['title'] = result['title']

            ta = TableAssembler(result, timerange=timerange)
            result_tables, result_fops = ta.get_bytes()

            for _result in result_tables:
                await bot.send_document(message.chat.id,
                                        InputFile(_result["workbooks_bytes"],
                                                  filename=f'Книга за {_result["workbooks_month"]}_'
                                                           f'{data["title"]}.xls'),
                                        caption=f"{get_missing_months(lost_months)}",
                                        parse_mode=ParseMode.HTML
                                        )

            if result_fops:
                await bot.send_document(message.chat.id, InputFile(result_fops,
                                                                   filename=f'4Дф {data["title"]}.txt'))

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
