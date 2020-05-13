from .base_context import BaseContext


class GlobalConfigContext(BaseContext):  # pylint: disable=too-few-public-methods
    def __init__(self, *args, debug, hdd_file, **kwargs):
        super().__init__(*args, **kwargs)
        self.debug = debug
        self.hdd_file = hdd_file
