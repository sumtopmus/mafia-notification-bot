from telegram.ext import ContextTypes
from typing import Dict


def list_nicknames(context: ContextTypes.DEFAULT_TYPE) -> Dict[str, int]:
    """List all nicknames."""
    return {
        player.get("nickname", str(id)): id
        for id, player in context.bot_data["players"].items()
    }
