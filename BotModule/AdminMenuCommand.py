from aiogram.dispatcher import FSMContext
from aiogram.types import Message, ContentType, ParseMode, CallbackQuery
from aiogram.utils.exceptions import MessageCantBeEdited

from BotModule import logger, dp, bot, commands
from BotModule.Keyboards import get_menu, get_users, user_detail_keyboard
from BotModule.States import AdminMenu
from DBAPI.DBClient import DBClient
from DBAPI.DBExceptions import UserNotExists


@logger.catch
@dp.message_handler(commands=['AdminMenu'], state='*')
async def start_menu_command(message: Message):

    user = DBClient().get_user(message.chat.id)

    if not user.isAdmin:
        await bot.send_message(message.chat.id, "Для доступа к данному меню нужно иметь права администратора.")
        return

    await AdminMenu.main.set()
    await bot.send_message(message.chat.id, 'Приветствую! Вы находитесь в меню для администраторов.',
                           reply_markup=get_menu())


@logger.catch
@dp.callback_query_handler(lambda call: call.data == 'userlist', state=AdminMenu.main)
async def user_list(call: CallbackQuery):
    users = DBClient().get_users()

    await AdminMenu.users.set()
    await bot.edit_message_text('Список пользователей: ', call.message.chat.id, call.message.message_id,
                                reply_markup=get_users(users))


@logger.catch
@dp.callback_query_handler(lambda call: call.data.startswith('user_'), state=AdminMenu.users)
async def user_detail(call: CallbackQuery, state: FSMContext):

    user_id = int(call.data.replace('user_', ''))
    user = DBClient().get_user(user_id)

    async with state.proxy() as data:
        data['user_id'] = user_id

    await send_message_detail(user, call.message.chat.id,
                              call.message.message_id)


async def send_message_detail(user, user_id, message_id):

    await AdminMenu.user_details.set()

    who_added = user.addedByUserID
    try:
        user_who_added = f'@{DBClient().get_user(who_added).Username}'
    except UserNotExists:
        user_who_added = f'@Nobody'

    msg_text = (f'Имя: <b>{user.Name}</b>\n'
                f'Юзернейм: <b>@{user.Username}</b>\n'
                f'Идентификатор: <b>{user.User_ID}</b>\n'
                f'Администратор: <b>{"Да" if user.isAdmin else "Нет"}</b>\n'
                f'Последний вход: <b>{user.LastLogged}</b>\n'
                f'Кто пригласил: <b>{user_who_added}</b>')

    try:
        await bot.edit_message_text(msg_text,
                                    user_id,
                                    message_id,
                                    reply_markup=user_detail_keyboard(user),
                                    parse_mode=ParseMode.HTML
                                    )
    except MessageCantBeEdited:
        await bot.send_message(user_id, msg_text,
                               reply_markup=user_detail_keyboard(user),
                               parse_mode=ParseMode.HTML)


@logger.catch
@dp.callback_query_handler(lambda call: call.data.startswith('change_name'), state=AdminMenu.user_details)
async def press_button_change_name(call: CallbackQuery):
    await AdminMenu.check_name.set()

    await bot.edit_message_text('Введите новое имя для пользователя:',
                                call.message.chat.id,
                                call.message.message_id,
                                parse_mode=ParseMode.HTML
                                )


@logger.catch
@dp.message_handler(lambda message: message.text not in commands,
                    content_types=ContentType.TEXT, state=AdminMenu.check_name)
async def change_name(message: Message, state: FSMContext):
    async with state.proxy() as data:
        user_id = data['user_id']

    DBClient().change_name(user_id, message.text)
    user = DBClient().get_user(user_id)

    await send_message_detail(user, message.chat.id,
                              message.message_id)


@logger.catch
@dp.callback_query_handler(lambda call: call.data == 'change_admin', state=AdminMenu.user_details)
async def press_button_change_admin(call: CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        user_id = data['user_id']

    DBClient().is_admin_reverse(user_id)

    user = DBClient().get_user(user_id)

    await send_message_detail(user, call.message.chat.id,
                              call.message.message_id)


@logger.catch
@dp.callback_query_handler(lambda call: call.data.startswith('backTo_'), state=AdminMenu)
async def backTo(call: CallbackQuery):
    if call.data == "backTo_userList":
        await user_list(call)


@logger.catch
@dp.callback_query_handler(lambda call: call.data == 'addUser', state=AdminMenu.main)
async def addNew_user(call: CallbackQuery):
    await AdminMenu.add_new_user.set()

    await bot.edit_message_text('Для добавления нового пользователя перешлите мне любое его сообщение.',
                                call.message.chat.id,
                                call.message.message_id,
                                parse_mode=ParseMode.HTML
                                )


@logger.catch
@dp.message_handler(lambda message: message.text not in commands,
                    content_types=ContentType.TEXT, state=AdminMenu.add_new_user)
async def addNew_user(message: Message, state: FSMContext):
    forward_sender_id = message.forward_from.id
    forward_sender_name = message.forward_from.username

    DBClient().add_user(forward_sender_id, forward_sender_name, False, addedBy=message.chat.id)

    async with state.proxy() as data:
        data['user_id'] = forward_sender_id

    user = DBClient().get_user(forward_sender_id)

    await send_message_detail(user, message.chat.id,
                              message.message_id)

