from .contexts import ContextCollection
from .helpers import BOOLEAN_RULE, MANDATORY_STRING_RULE, DocumentValidationException, validate
from .tasks import BaseTask
from .helpers import AppException


class BuildException(AppException):
    pass


class InvalidConfigurationException(BuildException):
    @staticmethod
    def format(header, error: AppException):
        lines = error.message().splitlines()
        lines.insert(0, header)
        return "\n  ".join(lines)

    @classmethod
    def on_global(cls, error: AppException):
        return cls(InvalidConfigurationException.format("Configuration is invalid:", error))

    @classmethod
    def on_task(cls, task_name, error: AppException):
        return cls(InvalidConfigurationException.format("Task '{}' configuration is invalid:".format(task_name), error))

    @classmethod
    def on_task_unsupported(cls, task_name):
        return cls("Task '{}' is not supported".format(task_name))


class VmBuilder:
    __task_names = []
    __task_types = []
    __task_types_by_name = {}
    __task_schemas_by_name = {}

    for task_type in BaseTask.__subclasses__():
        task_name = task_type.task_name()
        __task_names.append(task_name)
        __task_types.append(task_type)
        __task_types_by_name[task_name] = task_type
        __task_schemas_by_name[task_name] = task_type.schema()

    __global_schema = {
        "debug": BOOLEAN_RULE,
        "hdd-file": MANDATORY_STRING_RULE,
        "tasks": {
            "type": "list",
            "schema": {"type": "dict", "allow_unknown": True, "schema": {"task": {"type": "string", "allowed": __task_names}}},
        },
    }

    def __init__(self, global_config):
        self.tasks = []

        try:
            global_config_coerced = validate(VmBuilder.__global_schema, global_config)
        except DocumentValidationException as error:
            raise InvalidConfigurationException.on_global(error).log()

        task_configs = global_config_coerced.pop("tasks")

        self.ctx = ContextCollection(global_config_coerced)

        for task_config in task_configs:
            task_name = task_config.pop("task")
            self.add_task(task_name, task_config)

    def add_task(self, task_name, task_config):
        try:
            task_schema = VmBuilder.__task_schemas_by_name[task_name]
        except KeyError:
            raise InvalidConfigurationException.on_task_unsupported(task_name).log()

        try:
            task_config_coerced = validate(task_schema, task_config)
        except DocumentValidationException as error:
            raise InvalidConfigurationException.on_task(task_name, error).log()

        task_type = VmBuilder.__task_types_by_name[task_name]
        task = task_type(task_config_coerced, self.ctx)

        self.tasks.append(task)

    def system_check(self):
        for task in self.tasks:
            self.ctx.log.message("System check for task '{}'", task.__class__.task_name())
            task.system_check()

    def run_task(self, task):
        self.ctx.log.message("Running task '{}'", task.__class__.task_name())
        task.run()

    def run(self):
        while self.tasks:
            if not self.tasks[0].needs_chroot():
                self.run_task(self.tasks.pop(0))
            else:
                with self.ctx.execution.chroot_mount():
                    while self.tasks:
                        if not self.tasks[0].needs_chroot():
                            break

                        self.run_task(self.tasks.pop(0))

    def build(self):
        try:
            self.system_check()
            self.run()
        except AppException as error:
            raise BuildException(error).log(self.ctx.log.error)
        finally:
            self.ctx.log.debug(self.ctx.shell.program_usages())
