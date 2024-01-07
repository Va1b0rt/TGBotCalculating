import datetime
from urllib.parse import quote

from aiogram.types import InputMediaDocument, InputFile, Message, ParseMode
from dateutil.relativedelta import relativedelta

from BotModule import bot, dp
from BotModule.States import StatesMenu
from Exceptions import NoWorkers, WorkerNotHaveWorkHours
from cloud_sheets import Employers
from tables.settlement_payment import SettlementPayment
from tables.working_hour_sheet import AppearanceOTWHSheet


async def send_document_group(chat_id, documents, title: str):
    media = []
    actual_month = (datetime.datetime.now() - relativedelta(months=1)).month
    for num, document_data in enumerate(documents):
        message = ''
        file_name = quote(f'Табель {actual_month} {title}.xlsx'.replace(' ', '_'))
        if num == 0:
            message = f'{title}'
            file_name = quote(f'Расчётно-платёжная {title}.xlsx'.replace(' ', '_'))

        media.append(InputMediaDocument(media=InputFile(document_data, filename=file_name),
                                        caption=message))

    await bot.send_media_group(chat_id=chat_id, media=media)


@dp.message_handler(commands=['test_command'], state='*')
async def start_message_command(message: Message):
    await StatesMenu.test_state.set()
    await bot.send_message(message.chat.id, 'Генерируем пакет документов.')

    employers = Employers()

    for employer in employers.get_employers():
        if len(employer.workers) == 0:
            await bot.send_message(message.chat.id, f'❌ <b>{employer.name}</b> не имеет сотрудников.',
                                   parse_mode=ParseMode.HTML)
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
                                   parse_mode=ParseMode.HTML)
        except WorkerNotHaveWorkHours as ex:
            await bot.send_message(message.chat.id,
                                   f'❌ У <b>{employer.name} > {ex.worker.name}</b> не проставлены часы в таблице. \n'
                                   f'К сожалению без указания этих данных я не смогу сгенерировать таблицы.\n'
                                   f'Заполните недостающие данные и попробуйте сгенерировать таблицы снова.',
                                   parse_mode=ParseMode.HTML)
