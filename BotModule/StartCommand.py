from aiogram.types import Message

from BotModule import dp, bot
from states import StatesMenu


@dp.message_handler(commands=['start'], state='*')
async def start_message_command(message: Message):
    await StatesMenu.main.set()
    await bot.send_message(message.chat.id,
                           'Вас приветствует бот для расчёта данных из выписок.'
                           )
