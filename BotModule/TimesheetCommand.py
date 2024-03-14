import json

from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery, ContentType, ParseMode, InputFile

from BotModule import dp, bot, logger, commands
from BotModule.Common import get_message, find_entrepreneur, get_missing_months
from BotModule.Keyboards import keyboard_handle_extracts_timesheet, entrepreneurs_menu
from BotModule.States import StatesMenu
from Exceptions import NotHaveTemplate, UnknownEncoding, TemplateDoesNotFit, NoColumn
from XLAssembler import TableAssembler
from calculating import get_timesheet_data
from cloud_sheets import Entrepreneurs


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
                             parse_mode=ParseMode.HTML)


@logger.catch
@dp.callback_query_handler(lambda call: call.data.startswith('fop_'), state=StatesMenu.timesheet_get_extras)
async def pressed_button_fop(call: CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        _, data['title'], data['holder_id'] = call.data.split('_')

    await bot.edit_message_text(f'Выписки в количестве <b>{len(data["extracts"])}шт.</b>\n'
                                f'Имя владельца выписки: <b>{data["title"]}</b>\n'
                                '<b>Обрабатываем...</b>',
                                call.message.chat.id, call.message.message_id,
                                parse_mode=ParseMode.HTML)

    await generate_timesheet(data, call.message)


@logger.catch
@dp.callback_query_handler(lambda call: call.data == "button_handle_extracts_timesheet",
                           state=StatesMenu.timesheet_get_extras)
async def button_upload_timesheet(call: CallbackQuery, state: FSMContext):
    entrepreneurs = Entrepreneurs()

    async with state.proxy() as data:
        if "title" not in data:

            await bot.send_message(call.message.chat.id,
                                   f'⚠ <b>Обратите внимание, что вы не указали имя владельца выписки.</b> ⚠\n'
                                   'Без указания этой информации мы не сможем правильно обработать выписки.\n'
                                   'Выберите из предложенного ниже списка нужного предпринимателя.'
                                   f'{get_message(data)}',
                                   reply_markup=entrepreneurs_menu(entrepreneurs),
                                   parse_mode=ParseMode.HTML)
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

        if 'extracts' in data and data['extracts']:
            await bot.edit_message_text(f'Выписки в количестве <b>{len(data["extracts"])}шт.</b>\n'
                                        f'Имя владельца выписки: <b>{data["title"]}</b>\n'
                                        '<b>Обрабатываем...</b>',
                                        call.message.chat.id, call.message.message_id,
                                        parse_mode=ParseMode.HTML)
            await generate_timesheet(data, call.message)
        else:
            await bot.send_message(call.message.chat.id, 'Полученные данные неверны.')
            await StatesMenu.main.set()


@logger.catch
@dp.message_handler(lambda message: message.text not in commands,
                    content_types=ContentType.TEXT, state=StatesMenu.timesheet_get_extras)
async def handle_tittle_question(message: Message, state: FSMContext):
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
                                   # reply_markup=keyboard_handle_extracts_timesheet,
                                   reply_markup=entrepreneurs_menu(entrepreneurs),
                                   parse_mode=ParseMode.HTML)
            return

        data['title'], data['holder_id'] = entrepreneur.split('_')

        await message.answer(f'Имя владельца выписки было успешно обновлено.\n'
                             f'{get_message(data)}',
                             reply_markup=keyboard_handle_extracts_timesheet,
                             parse_mode=ParseMode.HTML)


async def generate_timesheet(data, message):
    await message.answer('Обрабатываем...')

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

        result, _, timerange, lost_months = await get_timesheet_data(extracts_files, 'timesheet',
                                                                     title=data['title'], holder_id=data['holder_id'])

        ta = TableAssembler(result, timerange=timerange)
        result_tables, result_fops = ta.get_bytes()

        if result_tables:
            for result in result_tables:
                await bot.send_document(message.chat.id,
                                        InputFile(result["workbooks_bytes"],
                                                  filename=f'Книга за {result["workbooks_month"]}_'
                                                           f'{data["title"]}.xls'),
                                        caption=f"{get_missing_months(lost_months)}",
                                        parse_mode=ParseMode.HTML)
        else:
            await bot.send_message(message.chat.id,
                                   'Исходя из значений данной выписки была сгенерирована пустая таблица.'
                                   'Скорее всего набор значений данной выписки является неполным или повреждённым.')

        if result_fops:
            await bot.send_document(message.chat.id, InputFile(result_fops,
                                                               filename=f'4Дф_{data["title"]}.txt'))

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
        logger.exception(ex)
    await StatesMenu.main.set()


@logger.catch
@dp.callback_query_handler(lambda call: call.data.startswith("entrepreneurs_menu:"),
                           state='*')
async def button_entrepreneurs_menu(call: CallbackQuery):
    entrepreneurs = Entrepreneurs()

    remover = int(call.data.replace('entrepreneurs_menu:', ''))

    await bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id,
                                        reply_markup=entrepreneurs_menu(entrepreneurs, remover=remover))
