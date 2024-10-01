from .debug import error_handler

from . import debug
from . import nickname
from . import notify
from . import poll


__all__ = ["all", "error_handler", "notify", "poll"]

# Business logic handlers
logic_handlers = []
modules = [nickname, notify, poll]
for module in modules:
    logic_handlers.extend(module.create_handlers())
# All handlers (debug + logic)
all = debug.handlers + logic_handlers
