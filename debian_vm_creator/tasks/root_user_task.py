import os

from ..contexts import ShellException
from ..helpers import BOOLEAN_RULE, MANDATORY_STRING_RULE, OPTIONAL_STRING_RULE
from .base_task import BaseTask


class RootUserTask(BaseTask):
    @staticmethod
    def name():
        return "root-user"

    @staticmethod
    def schema():
        return {"key": OPTIONAL_STRING_RULE, "password": {"oneof": [BOOLEAN_RULE, MANDATORY_STRING_RULE]}}

    def system_check(self):
        self.ctx.shell.require_programs("mkdir", "chmod")

    def needs_chroot(self):
        return True

    def run(self):
        key = self.config["key"]
        password = self.config["password"]

        if isinstance(password, (bool)):
            if password:
                self.ctx.log.debug("Asking for root password")

                while True:
                    try:
                        self.ctx.shell.execute_chroot("passwd")
                    except ShellException:
                        pass
                    else:
                        break
        else:
            self.ctx.log.debug("Setting root password to ****")
            self.ctx.shell.execute_chroot("passwd", input="{0}\n{0}".format(password), silent=True)

        if key:
            self.ctx.log.debug("Installing ssh key for user root")
            self.__install_key("root", "/root", key)

    def __install_key(self, user, home, key):
        ssh_dir = os.path.join(home, ".ssh")
        ssh_dir_chroot = self.ctx.execution.chroot_path(ssh_dir)
        authorized_keys_file = os.path.join(ssh_dir_chroot, "authorized_keys")

        self.ctx.shell.execute("mkdir", "-p", ssh_dir_chroot)

        authorized_keys = set()

        try:
            with open(authorized_keys_file, "r") as stream:
                for existing_key in stream.read().splitlines():
                    authorized_keys.add(existing_key.strip() + os.linesep)
        except FileNotFoundError:
            pass

        authorized_keys.add(key.strip() + os.linesep)

        with open(authorized_keys_file, "w") as stream:
            stream.writelines(authorized_keys)

        self.ctx.shell.execute("chmod", "-R", "a=,u+rwX", ssh_dir_chroot)
        self.ctx.shell.execute_chroot("chown", "-R", user, ssh_dir)
