from enum import Enum
from telegram import Update
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    filters,
    MessageHandler,
    TypeHandler,
)

from config import settings
from model.utils import list_nicknames
from utils import log


State = Enum("State", ["AWAITING"])


def create_handlers() -> list:
    """Creates handlers that process /nickname command."""
    return [
        ConversationHandler(
            entry_points=[CommandHandler("nickname", on_nickname)],
            states={
                State.AWAITING: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE,
                        add_or_change_nickname,
                    )
                ],
                ConversationHandler.TIMEOUT: [TypeHandler(Update, timeout)],
            },
            fallbacks=[CommandHandler("cancel", cancel)],
            allow_reentry=True,
            conversation_timeout=settings.CONVERSATION_TIMEOUT,
            name="nickname",
            per_chat=False,
        )
    ]


async def on_nickname(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """When user uses /nickname command."""
    log("on_nickname")
    message = "Будь ласка, введіть ваш нік."
    await update.effective_user.send_message(message)
    return State.AWAITING


async def add_or_change_nickname(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> State:
    """When user enters a nickname."""
    log("add_or_change_nickname")
    user = update.effective_user
    nickname = update.message.text
    user_with_this_nickname = list_nicknames(context).get(nickname, user.id)
    if user_with_this_nickname != user.id:
        message = "Цей нік вже зайнятий. Будь ласка, виберіть інший."
        await user.send_message(message)
        return State.AWAITING
    context.bot_data["players"].setdefault(user.id, {})["nickname"] = nickname
    message = f"Вітаю, {nickname}!"
    await update.effective_user.send_message(message)
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When a user cancels the conversation."""
    log("cancel")
    message = "Операцію скасовано."
    await update.effective_user.send_message(message)
    return ConversationHandler.END


async def timeout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """When the conversation timepout is exceeded."""
    log("timeout")
    message = "Запит скасовано автоматично через таймаут."
    await update.effective_user.send_message(message)
    return ConversationHandler.END
