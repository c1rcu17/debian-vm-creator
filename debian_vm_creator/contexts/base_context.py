from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .context_collection import ContextCollection


class BaseContext:  # pylint: disable=too-few-public-methods
    def __init__(self, context_collection: "ContextCollection"):
        self.ctx = context_collection

    def __str__(self):
        exclude_fields = ["ctx"]

        return str(
            {
                attr: getattr(self, attr)
                for attr in dir(self)
                if not attr.startswith("__") and attr not in exclude_fields and not callable(getattr(self, attr))
            }
        )
