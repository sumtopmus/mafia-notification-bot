from datetime import datetime
from enum import Enum
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatMemberStatus
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    ChatJoinRequestHandler,
    ChatMemberHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    filters,
    MessageHandler,
    TypeHandler,
)
from telegram.error import Forbidden, TelegramError

from config import settings
from model.utils import list_nicknames
import utils


Action = Enum(
    "Action",
    [
        # Button action:
        "SKIP",
        "MR",
        "MS",
    ],
)


State = Enum(
    "State",
    [
        # Particular states:
        "WAITING_FOR_NICKNAME",
        "WAITING_FOR_TITLE",
    ],
)


UserStatus = Enum(
    "UserStatus",
    [
        # User statuses:
        "OTHER",
        "NEW_MEMBER",
    ],
)


def create_handlers() -> list:
    """Creates handlers that process join requests."""
    return [
        ConversationHandler(
            entry_points=[
                MessageHandler(
                    filters.Chat(settings.CLUB_CHAT_ID)
                    & filters.StatusUpdate.NEW_CHAT_MEMBERS,
                    join,
                ),
                MessageHandler(
                    filters.Chat(settings.CLUB_CHAT_ID)
                    & filters.StatusUpdate.LEFT_CHAT_MEMBER,
                    left,
                ),
                ChatJoinRequestHandler(join_request, chat_id=settings.CLUB_CHAT_ID),
                CommandHandler(
                    "join", join_request, ~filters.Chat(settings.CLUB_CHAT_ID)
                ),
            ],
            states={
                State.WAITING_FOR_NICKNAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, set_nickname)
                ],
                State.WAITING_FOR_TITLE: [CallbackQueryHandler(set_title)],
                ConversationHandler.TIMEOUT: [TypeHandler(Update, timeout)],
            },
            fallbacks=[
                CommandHandler("cancel", cancel, ~filters.Chat(settings.CLUB_CHAT_ID)),
            ],
            allow_reentry=True,
            conversation_timeout=settings.WELCOME_TIMEOUT,
            name="welcome",
            per_chat=False,
            persistent=True,
        )
    ]


async def left(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When a user leaves the chat."""
    utils.log("left")
    if update.message.from_user != update.message.left_chat_member:
        await update.message.delete()
    return ConversationHandler.END


async def join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When a user joins the chat (by message)."""
    utils.log("join")
    questionnaire_initiated = False
    for user in update.message.new_chat_members:
        utils.log(f"{utils.user_repr(user)} joined the chat", logging.INFO)
        if user.is_bot:
            utils.log(f"new user is a bot")
            continue
        if (
            user.id not in context.bot_data["players"]
            or not context.bot_data["players"][user.id]["answered"]
        ):
            await update.message.delete()
            try:
                await initiate_questionnaire(update, context)
                utils.log(
                    f"{utils.user_repr(user)} is given the questionnaire", logging.INFO
                )
                questionnaire_initiated = True
            except Forbidden as e:
                message = f"{utils.mention(user)} намагається додатись до чату Capitol Mafia, але бот не може надсилати цьому користувачу повідомлення."
                await context.bot.send_message(settings.ADMINS[0], message)
                utils.log(
                    f"{utils.user_repr(user)} cannot receive the bot's messages ({e})",
                    logging.ERROR,
                )
            await context.bot.ban_chat_member(update.message.chat.id, user.id)
            await context.bot.unban_chat_member(update.message.chat.id, user.id)
            utils.log(f"{utils.user_repr(user)} is kicked", logging.INFO)
            continue
        titled_mention = context.bot_data["players"][user.id]["nickname"]
        title = context.bot_data["players"][user.id]["title"]
        if title:
            titled_mention = title + " " + titled_mention
        if context.bot_data["players"][user.id]["introduced"]:
            utils.log(
                f"{utils.user_repr(user)} already introduced themselves", logging.INFO
            )
            message = (
                "Ви тільки подивіться, хто до нас повернувся! Аплодисменти!\n\n"
                f"Зустрічайте – {titled_mention} ({user.mention_markdown()})!"
            )
            utils.log(message)
            await context.bot.sendMessage(
                chat_id=update.message.chat.id,
                text=message,
                reply_to_message_id=update.message.id,
            )
            continue
        message = (
            "В нашому клубі нові люди!\n\n"
            f"Зустрічайте – {titled_mention} ({user.mention_markdown()})!\n\n"
            "_#about_"
        )
        await context.bot.sendMessage(
            chat_id=update.message.chat.id,
            text=message,
            reply_to_message_id=update.message.id,
        )
        context.bot_data["players"][user.id]["introduced"] = True
    if questionnaire_initiated:
        return State.WAITING_FOR_NICKNAME
    return ConversationHandler.END


async def join_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When a join request is sent."""
    utils.log("join_request")
    user = update.effective_user
    utils.log(f"{utils.user_repr(user)} requested to join the chat", logging.INFO)
    if (
        user.id in context.bot_data["players"]
        and context.bot_data["players"][user.id]["answered"]
    ):
        try:
            await user.approve_join_request(settings.CLUB_CHAT_ID)
            utils.log(
                f"{utils.user_repr(user)} already answered the questionnaire, the request is approved",
                logging.INFO,
            )
        except TelegramError as e:
            utils.log(f"No join requests found: {e}")
        return ConversationHandler.END
    return await initiate_questionnaire(update, context)


async def initiate_questionnaire(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> State:
    """Initiates the questionnaire."""
    utils.log("initiate_questionnaire")
    user = update.effective_user
    context.bot_data["players"].setdefault(
        user.id, {"first_join_timestamp": datetime.now().isoformat()}
    )
    context.bot_data["players"][user.id]["answered"] = False
    context.bot_data["players"][user.id]["introduced"] = False
    message = (
        f"Привіт, {user.full_name}! Клуб Capitol Mafia вітає вас! "
        "Підписуйтесь на наш канал, щоб слідкувати за ігровими вечорами в клубі.\n\n"
        "Щоб потрапити в наш чат, вам треба придумати собі ігровий нік. "
        "Бажано, щоб це було не ваше імʼя, а щось цікаве і унікальне.\n\n"
        "Ітак, яким буде ваш нік?"
    )
    channel = await context.bot.get_chat(settings.CLUB_CHANNEL)
    keyboard = [[InlineKeyboardButton(text="Підписатися на канал", url=channel.link)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await user.send_message(message, reply_markup=reply_markup)
    return State.WAITING_FOR_NICKNAME


async def set_nickname(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When the nickname is submitted."""
    utils.log("set_nickname")
    user = update.effective_user
    nickname = update.message.text
    user_with_this_nickname = list_nicknames(context).get(nickname, user.id)
    if user_with_this_nickname != user.id:
        message = "Цей нік вже зайнятий. Будь ласка, виберіть інший."
        await user.send_message(message)
        return State.WAITING_FOR_NICKNAME
    context.bot_data["players"][user.id]["nickname"] = nickname
    message = f"Якому звертанню ви надаєте перевагу?"
    keyboard = [
        [
            InlineKeyboardButton("Пан", callback_data=Action.MR.name),
            InlineKeyboardButton("Пані", callback_data=Action.MS.name),
        ],
        [InlineKeyboardButton("Пропустити", callback_data=Action.SKIP.name)],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await user.send_message(message, reply_markup=reply_markup)
    return State.WAITING_FOR_TITLE


async def set_title(update: Update, context: CallbackContext) -> State:
    """When the title is submitted."""
    utils.log("set_title")
    await update.callback_query.answer()
    user = update.effective_user
    if update.callback_query.data == Action.MR.name:
        context.bot_data["players"][user.id]["title"] = "пан"
    elif update.callback_query.data == Action.MS.name:
        context.bot_data["players"][user.id]["title"] = "пані"
    else:
        context.bot_data["players"][user.id]["title"] = None
    context.bot_data["players"][user.id]["answered"] = True
    try:
        await user.approve_join_request(settings.CLUB_CHAT_ID)
        utils.log(
            f"{utils.user_repr(user)} just finished the questionnaire, the request is approved",
            logging.INFO,
        )
    except TelegramError as e:
        utils.log(f"No join requests found: {e}")
    message = f"Дякуємо! Тепер ви можете користуватись нашим чатом."
    keyboard = [
        [InlineKeyboardButton(text="Перейти до чату", url=settings.CHAT_INVITE_LINK)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await user.send_message(message, reply_markup=reply_markup)
    return ConversationHandler.END


async def timeout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """When the conversation timepout is exceeded."""
    utils.log("timeout")
    user = update.effective_user
    message = (
        "Вже пройшла доба, а ви все ще не вказали свій нік. "
        "Вашу заявку було відхилено, проте ви завжди можете податися в клуб знову, "
        "нажавши /join."
    )
    await user.send_message(message)
    try:
        await user.decline_join_request(settings.CLUB_CHAT_ID)
    except TelegramError as e:
        utils.log(f"No join requests found: {e}")
    utils.log(
        f"{utils.user_repr(user)} timed out, the request is declined", logging.INFO
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """When a user cancels the process."""
    utils.log("cancel")
    message = "Ви можете податися в клуб знову, нажавши /join."
    await update.effective_user.send_message(message)
    if update.chat_join_request:
        await update.chat_join_request.from_user.decline_join_request(
            update.chat_join_request.chat.id
        )
    return ConversationHandler.END
