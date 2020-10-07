from ..helpers import MANDATORY_STRING_RULE
from .base_task import BaseTask


KEYBOARD = """\
XKBMODEL="{{ model }}"
XKBLAYOUT="{{ layout }}"
XKBVARIANT=""
XKBOPTIONS=""
BACKSPACE="guess"
"""


class KeyboardTask(BaseTask):
    @staticmethod
    def task_name():
        return "keyboard"

    @staticmethod
    def schema():
        return {"model": MANDATORY_STRING_RULE, "layout": MANDATORY_STRING_RULE}

    def system_check(self):
        pass

    def needs_chroot(self):
        return True

    def run(self):
        model = self.config["model"]
        layout = self.config["layout"]

        self.ctx.log.debug("Setting keyboard model to {} and layout to {}", model, layout)
        self.ctx.debian.apt_install("keyboard-configuration", show_dialogs=False)
        self.ctx.template.render_to_file(KEYBOARD, "/etc/default/keyboard", model=model, layout=layout)
        self.ctx.debian.dpkg_reconfigure("keyboard-configuration", show_dialogs=False)
