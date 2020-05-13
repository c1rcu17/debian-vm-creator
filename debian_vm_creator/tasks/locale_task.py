import os

from ..helpers import MANDATORY_STRING_RULE
from .base_task import BaseTask


LOCALE_GEN = """\
{{ default }} UTF-8
{{ formats }} UTF-8
"""

LOCALE = """\
LANG={{ default }}
LANGUAGE={{ language }}
LC_CTYPE={{ formats }}
LC_NUMERIC={{ formats }}
LC_TIME={{ formats }}
LC_COLLATE={{ formats }}
LC_MONETARY={{ formats }}
LC_MESSAGES={{ default }}
LC_PAPER={{ formats }}
LC_NAME={{ formats }}
LC_ADDRESS={{ formats }}
LC_TELEPHONE={{ formats }}
LC_MEASUREMENT={{ formats }}
LC_IDENTIFICATION={{ formats }}
"""


class LocaleTask(BaseTask):
    @staticmethod
    def name():
        return "locale"

    @staticmethod
    def schema():
        return {"default": MANDATORY_STRING_RULE, "formats": MANDATORY_STRING_RULE, "language": MANDATORY_STRING_RULE}

    def system_check(self):
        self.ctx.shell.require_programs("rm")

    def needs_chroot(self):
        return True

    def run(self):
        # https://www.ibm.com/support/knowledgecenter/en/ssw_aix_71/globalization/understand_locale_environ_var.html

        default = self.config["default"]
        formats = self.config["formats"]
        language = self.config["language"]
        locale_cache_dir = self.ctx.execution.chroot_path("/usr/lib/locale")

        self.ctx.log.debug("Setting default locale to {}, formats to {} and language to {}", default, formats, language)
        self.ctx.debian.apt_install("locales", show_dialogs=False, no_locale=True)
        self.ctx.shell.execute("rm", "-rfv", *[os.path.join(locale_cache_dir, f) for f in os.listdir(locale_cache_dir)])
        self.ctx.template.render_to_file(LOCALE_GEN, "/etc/locale.gen", default=default, formats=formats)
        self.ctx.template.render_to_file(LOCALE, "/etc/default/locale", default=default, formats=formats, language=language)
        self.ctx.debian.dpkg_reconfigure("locales", show_dialogs=False, no_locale=True)
