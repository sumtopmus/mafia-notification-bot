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
from telegram.helpers import escape_markdown
from typing import Dict

from config import settings
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
    message = escape_markdown("Будь ласка, введіть ваш нік.", version=2)
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
        message = escape_markdown(
            "Цей нік вже зайнятий. Будь ласка, виберіть інший.", version=2
        )
        await user.send_message(message)
        return State.AWAITING
    context.bot_data["players"].setdefault(user.id, {})["nickname"] = nickname
    message = escape_markdown(f"Вітаю, {nickname}!", version=2)
    await update.effective_user.send_message(message)
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """When a user cancels the conversation."""
    log("cancel")
    message = escape_markdown("Операцію скасовано.", version=2)
    await update.effective_user.send_message(message)
    return ConversationHandler.END


async def timeout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """When the conversation timepout is exceeded."""
    log("timeout")
    message = escape_markdown("Запит скасовано автоматично через таймаут.", version=2)
    await update.effective_user.send_message(message)
    return ConversationHandler.END


def list_nicknames(context: ContextTypes.DEFAULT_TYPE) -> Dict[str, int]:
    """List all nicknames."""
    return {
        player["nickname"]: id for id, player in context.bot_data["players"].items()
    }
