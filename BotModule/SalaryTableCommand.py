from aiogram.types import InputMediaDocument, InputFile, Message, ParseMode

from BotModule import dp, bot, logger
from BotModule.States import SalaryTableStates
from Exceptions import NoWorkers, WorkerNotHaveWorkHours
from cloud_sheets import Employers
from tables.Exceptions import NoSuitableEmployers
from tables.salary_table import SalaryTable


async def send_media(chat_id: int, media: list[InputMediaDocument]):
    buffer_media: list[InputMediaDocument] = []
    if len(media) > 10:
        for file in media:
            if len(buffer_media) == 10:
                await bot.send_media_group(chat_id=chat_id, media=buffer_media)
                buffer_media.clear()
            buffer_media.append(file)
        if buffer_media:
            await bot.send_media_group(chat_id=chat_id, media=buffer_media)

    else:
        await bot.send_media_group(chat_id=chat_id, media=media)


@dp.message_handler(commands=['salarytable'], state='*')
async def generate_salary_table_command(message: Message):
    await SalaryTableStates.start.set()

    employers = Employers()

    media = []

    for employer in employers.get_employers():
        if len(employer.workers) == 0:
            await bot.send_message(message.chat.id, f'❌ <b>{employer.name}</b> не имеет сотрудников.',
                                   parse_mode=ParseMode.HTML)
            continue

        try:
            table = SalaryTable(employer)
            media.append(InputMediaDocument(media=InputFile(table.file,
                                                            filename=f'Аванс_{employer.name}.xlsx'.replace(" ", "_")),
                                            caption=''))
        except NoSuitableEmployers as ex:
            await bot.send_message(message.chat.id,
                                   f'❌ <b>{ex.employer.name}</b> не имеет сотрудников, удовлетворяющих требованиям'
                                   f' для создания таблиц.',
                                   parse_mode=ParseMode.HTML)
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

    await send_media(message.chat.id, media)

