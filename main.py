from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ContentType, Message

from calculating import get_result
from XLAssembler import TableAssembler
from logger import Logger
from config import BOT_API_TOKEN

cls_logger = Logger()
logger = cls_logger.get_logger

bot = Bot(token=BOT_API_TOKEN)
dp = Dispatcher(bot)


@logger.catch
@dp.message_handler(content_types=ContentType.DOCUMENT)
async def handle_document(message: Message):
    document = message.document
    if document.mime_type == 'application/vnd.ms-excel':
        await message.answer('Получен XLS-файл. Обрабатываем...')
        file_id = document.file_id
        file_info = await bot.get_file(file_id)
        file_path = file_info.file_path
        file = await bot.download_file(file_path)
        result = get_result(file)

        ta = TableAssembler(result)
        result_table = ta.get_bytes()

        await bot.send_document(message.chat.id, types.InputFile(result_table, filename='RESULT.xls'))
        # await message.answer(f'Искомое значение: <code>{result}</code>', parse_mode=ParseMode.HTML)

    else:
        await message.answer('Прикреплённый файл не является XLS-файлом')
        logger.warning('Прикреплённый файл не является XLS-файлом')


if __name__ == "__main__":
    try:
        executor.start_polling(dp, skip_updates=True)
    except Exception as ex:
        logger.critical(ex)

    input("Нажмите Enter для завершения программы...")
