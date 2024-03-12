import hashlib
import io
from typing import Optional

from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery, ParseMode, InputFile

from BotModule import dp, bot, logger
from BotModule.Keyboards import entrepreneurs_keyboard, extracts_keyboard, extract_details_keyboard
from BotModule.States import EntrepreneursMenu
from DBAPI.DBClient import DBClient
from DBAPI.DBExceptions import NotExistsFourDF
from DBAPI.Models import Transaction as db_trans
from calculating import get_timerange, process_transactions, counting_revenue, add_list_fop_sums
from Models import Transaction


@dp.message_handler(commands=['menu'], state='*')
async def change_entrepreneurs_command(message: Message, call: CallbackQuery = None):
    try:
        entrepreneurs = DBClient().get_list_entrepreneurs()

        if not entrepreneurs:
            if call:
                await bot.edit_message_text(f'Для отображения этого меню вам нужно добавить хотя бы одну выписку, '
                                            f'для хотя бы одного предпринимателя.',
                                            call.message.chat.id,
                                            call.message.message_id)
                return
            await bot.send_message(message.chat.id,
                                   f'Для отображения этого меню вам нужно добавить хотя бы одну выписку, '
                                   f'для хотя бы одного предпринимателя.')
            return

        await EntrepreneursMenu.change_entrepreneur.set()
        if call:
            await bot.edit_message_text(f'Выберите предпринимателя из списка предложенного ниже.',
                                        call.message.chat.id,
                                        call.message.message_id,
                                        reply_markup=entrepreneurs_keyboard(entrepreneurs))
            return

        await bot.send_message(message.chat.id,
                               f'Выберите предпринимателя из списка предложенного ниже.',
                               reply_markup=entrepreneurs_keyboard(entrepreneurs))
    except Exception as ex:
        logger.exception(ex)
        await bot.send_message(message.chat.id,
                               f'К сожалению меню на данный момент недоступно.')


@logger.catch
@dp.callback_query_handler(lambda call: call.data.startswith('fop_'), state=EntrepreneursMenu.change_entrepreneur)
async def changed_entrepreneur(call: CallbackQuery, state: FSMContext):
    try:
        async with state.proxy() as data:
            _, data['title'], data['holder_id'] = call.data.split('_')

        extracts = DBClient().get_list_extracts(data['holder_id'])

        if not extracts:
            entrepreneurs = DBClient().get_list_entrepreneurs()
            await bot.edit_message_text(f'Для указанного предпринимателя нет ни одной выписки.\n'
                                        f'Выберите предпринимателя из списка предложенного ниже.',
                                        call.message.chat.id, call.message.message_id,
                                        reply_markup=entrepreneurs_keyboard(entrepreneurs))
            return

        await EntrepreneursMenu.extracts_menu.set()
        await bot.edit_message_text(f'Предприниматель <b>{data["title"]}</b> имеет'
                                    f'выписки в количестве <b>{len(extracts)}шт.</b>'
                                    'Выберите любую выписку из предложенных для просмотра деталей.',
                                    call.message.chat.id, call.message.message_id,
                                    reply_markup=extracts_keyboard(extracts),
                                    parse_mode=ParseMode.HTML)
    except Exception as ex:
        logger.exception(ex)
        await bot.edit_message_text(f'К сожалению не удалось получить список выписок для данного предпринимателя.',
                                    call.message.chat.id, call.message.message_id)


async def get_income(holder_id: int, title: str, extract_hash) -> Optional[float]:
    _transactions: list[db_trans] = DBClient().get_transactions(holder_id, extract_hash)

    transactions: list[Transaction] = []

    for tr in _transactions:
        transactions.append(Transaction(Extract_name=tr.Extract_name,
                                        Holder=title, Holder_id=tr.Holder_id,
                                        Date=tr.Date, Amount=tr.Amount,
                                        Purpose=tr.Purpose, Egrpou=f'{tr.EGRPOU}',
                                        Type="extract", Name=tr.Name,
                                        Hash=hashlib.sha256(f"{tr.Extract_name}{title}"
                                                            f"{tr.Holder_id}{tr.Date}{tr.Amount}{tr.Purpose}"
                                                            f"{tr.EGRPOU}{tr.Name}".encode()).hexdigest()))

    timerange = await get_timerange(transactions)

    try:
        timesheet_data, rows = process_transactions(int(holder_id))
    except:
        timesheet_data, rows = process_transactions(int(holder_id), ex_type='prro')

    timesheet_data = counting_revenue(timesheet_data)
    return round(float(timesheet_data['months'][timerange[1].month - 1]), 2)


@logger.catch
@dp.callback_query_handler(lambda call: call.data.startswith('ex_'), state=EntrepreneursMenu.extracts_menu)
async def changed_extract(call: CallbackQuery, state: FSMContext):
    try:
        async with state.proxy() as data:
            await EntrepreneursMenu.extract_detail.set()
            data['extract_hash'] = call.data.replace('ex_', "")

            details = DBClient().extract_details(data['extract_hash'], data['holder_id'])
            extract_name = DBClient().get_extract_name(data['extract_hash'], data['holder_id'])
            timerange = DBClient().get_extract_timerange(data['extract_hash'], data['holder_id'])

            extract_type = "Выписка" if details["extract_type"] == 'extract' else "ПРРО"

            income = await get_income(data['holder_id'], data["title"], data['extract_hash'])
            if income:
                await EntrepreneursMenu.extract_detail.set()
                await bot.edit_message_text(f'Предприниматель: <b>{data["title"]}</b>\n'
                                            f'Тип выписки: <b>{extract_type}</b>\n'
                                            f'Название выписки: <b>{extract_name}</b>\n'
                                            f'Количество транзакций: <b>{details["transactions_count"]}.шт</b>\n'
                                            f'Период: <b>{timerange}</b>\n'
                                            f'Доход: <b>{income}</b>',
                                            call.message.chat.id, call.message.message_id,
                                            reply_markup=extract_details_keyboard(data['extract_hash'], data['holder_id']),
                                            parse_mode=ParseMode.HTML)
            else:
                await pressed_back_button(call)

    except Exception as ex:
        logger.exception(ex)
        await bot.edit_message_text(f'Не удалось получить детализацию по выписке.',
                                    call.message.chat.id, call.message.message_id)


@logger.catch
@dp.callback_query_handler(lambda call: call.data.startswith('fourDF_'), state=EntrepreneursMenu.extract_detail)
async def upload_fourDF(call: CallbackQuery, state: FSMContext):
    extract_hash = call.data.replace('fourDF_', '')
    async with state.proxy() as data:
        holder_id = data['holder_id']

    try:
        fourDF = DBClient().get_fourDF(holder_id, extract_hash)
        fourDF_file_data = io.BytesIO()
        fourDF_file_data.write(fourDF.encode())
        fourDF_file_data.seek(0)

        await bot.send_document(call.message.chat.id, InputFile(fourDF_file_data,
                                                                filename=f'4Дф_{data["title"]}.txt'))
    except NotExistsFourDF:
        await bot.edit_message_text(f'⚠ Не удалось получить 4ДФ так-как он отсутствует в базе.',
                                    call.message.chat.id, call.message.message_id)
    except Exception as ex:
        logger.exception(ex)
        await bot.edit_message_text(f'⚠ Во время получения 4ДФ произошла неизвестная ошибка.',
                                    call.message.chat.id, call.message.message_id)


@logger.catch
@dp.callback_query_handler(lambda call: call.data.startswith('delete_extract_'), state=EntrepreneursMenu.extract_detail)
async def del_extract(call: CallbackQuery, state: FSMContext):
    extract_hash = call.data.replace('delete_extract_', '')
    await EntrepreneursMenu.extracts_menu.set()
    async with state.proxy() as data:
        holder_id = data['holder_id']
        extract_name = DBClient().get_extract_name(extract_hash, data['holder_id'])

    try:
        rows_deleted = DBClient().delete_extract(extract_name, holder_id)
        extracts = DBClient().get_list_extracts(holder_id)
        await bot.edit_message_text(f'Выписка <b>{extract_name}</b> была успешно удалена.\n'
                                    f'Всего удалено <b>{rows_deleted}</b> записей.',
                                    call.message.chat.id, call.message.message_id,
                                    reply_markup=extracts_keyboard(extracts),
                                    parse_mode=ParseMode.HTML)
        return

    except Exception as ex:
        logger.exception(ex)

        extract_name = DBClient().get_extract_name(extract_hash, data['holder_id'])
        details = DBClient().extract_details(extract_name, data['holder_id'])
        await bot.edit_message_text(f'Не удалось удалить: <b>{extract_name}</b>\n',
                                    f'Предприниматель: <b>{data["title"]}</b>\n'
                                    f'Название выписки: <b>{extract_name}шт.</b>'
                                    f'Количество транзакций: <b>{details["transactions_count"]}</b>'
                                    f'Период: <b>с по</b>',
                                    call.message.chat.id, call.message.message_id,
                                    reply_markup=extract_details_keyboard(extract_name, data['holder_id']),
                                    parse_mode=ParseMode.HTML)


@logger.catch
@dp.callback_query_handler(lambda call: call.data.startswith('back_extracts_'), state="*")
async def pressed_back_button(call: CallbackQuery):
    await change_entrepreneurs_command(call.message, call=call)
