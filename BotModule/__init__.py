import asyncio
import atexit

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.files import JSONStorage

from logger import Logger
from config import BOT_API_TOKEN


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
            '/bok_prro',
            '/get_empty_book',
            '/menu']


from . import StartCommand
from . import TimesheetCommand
from . import BookPRROCommand
from . import EmptyBookCommand
# from . import ExtractCommand
# from . import ExtractTestCommand
from . import MenuCommand
from . import TestCommand
