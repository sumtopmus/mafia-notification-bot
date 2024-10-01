from .error import handler as error_handler

from . import debug
from . import info
from . import upload

__all__ = ["error", "handler"]

# Debug handlers
handlers = []
for module in [debug, info, upload]:
    handlers.extend(module.create_handlers())
