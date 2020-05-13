from ..helpers import AppException
from .base_context import BaseContext


class DebianException(AppException):
    pass


class DebianContext(BaseContext):
    @staticmethod
    def __make_environment(*, show_dialogs=True, no_locale=False):
        environment = {}

        if not show_dialogs:
            environment["DEBIAN_FRONTEND"] = "noninteractive"

        if no_locale:
            environment["LC_ALL"] = "C"
            environment["LANGUAGE"] = "C"
            environment["LANG"] = "C"

        return environment

    def apt_update_packages_lists(self):
        self.ctx.shell.execute_chroot("apt-get", "update")

    def apt_is_installed(self, package):
        return self.ctx.shell.execute_chroot("dpkg", "-s", package, check=False, silent=True)

    def apt_install(self, *packages, **kwargs):
        for package in packages:
            if self.apt_is_installed(package):
                self.ctx.log.debug("Not installing already installed package {}", package)
            else:
                self.ctx.log.debug("Installing package {}", package)
                self.ctx.shell.execute_chroot("apt-get", "-y", "install", package, environment=DebianContext.__make_environment(**kwargs))

    def dpkg_reconfigure(self, *packages, **kwargs):
        self.ctx.shell.execute_chroot("dpkg-reconfigure", *packages, environment=DebianContext.__make_environment(**kwargs))
