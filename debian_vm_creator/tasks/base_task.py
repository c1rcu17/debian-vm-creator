from ..contexts import ContextCollection
from ..helpers import AppException


class TaskException(AppException):
    pass


class BaseTask:
    @staticmethod
    def task_name() -> str:
        raise NotImplementedError

    @staticmethod
    def schema() -> dict:
        raise NotImplementedError

    def __init__(self, task_config: dict, context_collection: ContextCollection):
        self.config = task_config
        self.ctx = context_collection

    def system_check(self) -> None:
        raise NotImplementedError

    def needs_chroot(self) -> bool:
        raise NotImplementedError

    def run(self) -> None:
        raise NotImplementedError
