import io

from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery, ParseMode, InputFile

from BotModule import dp, bot, logger
from BotModule.Keyboards import entrepreneurs_keyboard, extracts_keyboard, extract_details_keyboard
from BotModule.States import EntrepreneursMenu
from DBAPI.DBClient import DBClient
from DBAPI.DBExceptions import NotExistsFourDF


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

            await EntrepreneursMenu.extract_detail.set()
            await bot.edit_message_text(f'Предприниматель: <b>{data["title"]}</b>\n'
                                        f'Название выписки: <b>{extract_name}</b>\n'
                                        f'Количество транзакций: <b>{details["transactions_count"]}.шт</b>\n'
                                        f'Период: <b>{timerange}</b>',
                                        call.message.chat.id, call.message.message_id,
                                        reply_markup=extract_details_keyboard(data['extract_hash'], data['holder_id']),
                                        parse_mode=ParseMode.HTML)
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
        details = DBClient().extract_details(data['extract_name'], data['holder_id'])
        await bot.edit_message_text(f'Не удалось удалить: <b>{extract_name}</b>\n',
                                    f'Предприниматель: <b>{data["title"]}</b>\n'
                                    f'Название выписки: <b>{data["extract_name"]}шт.</b>'
                                    f'Количество транзакций: <b>{details["transactions_count"]}</b>'
                                    f'Период: <b>с по</b>',
                                    call.message.chat.id, call.message.message_id,
                                    reply_markup=extract_details_keyboard(data['extract_name']),
                                    parse_mode=ParseMode.HTML)


@logger.catch
@dp.callback_query_handler(lambda call: call.data.startswith('back_extracts_'), state="*")
async def pressed_back_button(call: CallbackQuery):
    await change_entrepreneurs_command(call.message, call=call)
