import asyncio
import atexit

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.files import JSONStorage
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.types import Message, CallbackQuery

from DBAPI.DBClient import DBClient
from DBAPI.DBExceptions import UserNotExists
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
            '/menu',
            '/test_command',
            '/AdminMenu',
            '/salarytable']


class LogInteractionTimeMiddleware(BaseMiddleware):
    async def on_pre_process_message(self, message: Message, data: dict):
        await self.log_interaction_time(message)

    async def on_pre_process_callback_query(self, query: types.CallbackQuery, data: dict):
        await self.log_interaction_time(query)

    async def log_interaction_time(self, message_or_query):
        if isinstance(message_or_query, types.Message):
            user_id = message_or_query.from_user.id
            username = message_or_query.from_user.username
        elif isinstance(message_or_query, types.CallbackQuery):
            user_id = message_or_query.from_user.id
            username = message_or_query.from_user.username
        else:
            user_id = None
            username = None

        if user_id is not None:
            try:
                DBClient().get_user(user_id)
            except UserNotExists:
                DBClient().add_user(user_id, username, False)

            DBClient().set_logged_time(user_id, username)


dp.middleware.setup(LogInteractionTimeMiddleware())


class CheckUserMiddleware(BaseMiddleware):
    async def on_pre_process_message(self, message: types.Message, data: dict):
        await self.check_user_exists(message)

    async def on_pre_process_callback_query(self, query: types.CallbackQuery, data: dict):
        await self.check_user_exists(query)

    async def check_user_exists(self, message_or_query):
        if isinstance(message_or_query, Message):
            user_id = message_or_query.from_user.id
        elif isinstance(message_or_query, CallbackQuery):
            user_id = message_or_query.from_user.id
        else:
            user_id = None

        if user_id is not None:
            try:
                user = DBClient().get_user(user_id)
                if not user.isAdmin:
                    await message_or_query.answer('')
            except UserNotExists:
                # If user does not exist, do not respond
                await message_or_query.answer('')
                return


dp.middleware.setup(CheckUserMiddleware())


from . import StartCommand
from . import TimesheetCommand
from . import BookPRROCommand
from . import EmptyBookCommand
# from . import ExtractCommand
# from . import ExtractTestCommand
from . import MenuCommand
from . import TestCommand
from . import AdminMenuCommand
from . import SalaryTableCommand


