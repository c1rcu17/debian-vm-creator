from .base_task import BaseTask


class ChrootTask(BaseTask):
    @staticmethod
    def name():
        return "chroot"

    @staticmethod
    def schema():
        return {}

    def system_check(self):
        pass

    def needs_chroot(self):
        return True

    def run(self):
        self.ctx.shell.execute_chroot("bash", check=False)
