from ..helpers import BOOLEAN_RULE
from .base_task import BaseTask


class SSHServerTask(BaseTask):
    @staticmethod
    def task_name():
        return "ssh-server"

    @staticmethod
    def schema():
        return {"password-login": BOOLEAN_RULE}

    def system_check(self):
        self.ctx.shell.require_programs("sed")

    def needs_chroot(self):
        return True

    def run(self):
        password_login = self.config["password-login"]
        sshd_config = self.ctx.execution.chroot_path("/etc/ssh/sshd_config")

        self.ctx.log.debug("Setting up SHH server")
        self.ctx.debian.apt_install("openssh-server")

        if password_login:
            self.ctx.shell.execute("sed", "-Ei", "s/^#?PermitRootLogin.*$/PermitRootLogin yes/", sshd_config)
        else:
            self.ctx.shell.execute("sed", "-Ei", "s/^#?PermitRootLogin.*$/PermitRootLogin prohibit-password/", sshd_config)
