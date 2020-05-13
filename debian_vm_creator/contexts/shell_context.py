import executor
import executor.chroot

from ..helpers import AppException
from .base_context import BaseContext

executor.DEFAULT_SHELL = "sh"


class ShellException(AppException):
    pass


class ProgramNotFoundException(ShellException):
    def __init__(self, program):
        super().__init__("Program '{}' not found".format(program))


class ShellContext(BaseContext):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__programs = {}

    def require_programs(self, *programs):
        for program in programs:
            if program in self.__programs:
                continue

            matches = executor.which(program)

            if len(matches) < 1:
                raise ProgramNotFoundException(program)

            self.__programs[program] = {"path": matches[0], "usages": 0, "checked": True}

    def program_usages(self):
        return "\n".join(
            ["{} {} ({}): {}".format("\u2714" if v["checked"] else "\u2716", k, v["path"], v["usages"]) for k, v in self.__programs.items()]
        )

    def execute(self, *command, **kw):
        program_name = command[0]

        if program_name not in self.__programs:
            self.require_programs(program_name)
            self.__programs[program_name]["checked"] = False

        program = self.__programs[program_name]
        program["usages"] += 1
        new_command = (program["path"], *command[1:])

        external_command = executor.ExternalCommand(*new_command, **kw)

        try:
            result = executor.execute_prepared(external_command)
        except executor.ExternalCommandFailed as error:
            raise ShellException(error)

        return result

    def execute_chroot(self, *command, **kw):
        chroot_command = executor.chroot.ChangeRootCommand(self.ctx.execution.workdir(), *command, **kw)

        try:
            result = executor.execute_prepared(chroot_command)
        except executor.ExternalCommandFailed as error:
            raise ShellException(error)

        return result
