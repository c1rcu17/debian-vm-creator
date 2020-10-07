from ..helpers import MANDATORY_STRING_RULE
from .base_task import BaseTask


TIMEZONE = """\
{{ timezone }}
"""


class TimezoneTask(BaseTask):
    @staticmethod
    def task_name():
        return "timezone"

    @staticmethod
    def schema():
        return {"timezone": MANDATORY_STRING_RULE}

    def system_check(self):
        self.ctx.shell.require_programs("ln")

    def needs_chroot(self):
        return True

    def run(self):
        timezone = self.config["timezone"]

        self.ctx.log.debug("Setting timezone to {}", timezone)
        self.ctx.debian.apt_install("tzdata")
        self.ctx.shell.execute("ln", "-sfn", "/usr/share/zoneinfo/{}".format(timezone), self.ctx.execution.chroot_path("/etc/localtime"))
        self.ctx.template.render_to_file(TIMEZONE, "/etc/timezone", timezone=timezone)
        self.ctx.debian.dpkg_reconfigure("tzdata", show_dialogs=False)
