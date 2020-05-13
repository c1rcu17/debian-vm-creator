from .debian_context import DebianContext
from .execution_context import ExecutionContext
from .global_config_context import GlobalConfigContext
from .log_context import LogContext
from .shell_context import ShellContext
from .template_context import TemplateContext


class ContextCollection:  # pylint: disable=too-few-public-methods
    def __init__(self, global_config):
        self.execution = ExecutionContext(self)
        self.global_config = GlobalConfigContext(self, debug=global_config["debug"], hdd_file=global_config["hdd-file"])
        self.log = LogContext(self)
        self.shell = ShellContext(self)
        self.template = TemplateContext(self)
        self.debian = DebianContext(self)
