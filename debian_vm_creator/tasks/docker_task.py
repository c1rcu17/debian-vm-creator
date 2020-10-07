import os
import shutil

from ..helpers import BOOLEAN_RULE, POSITIVE_INTEGER_RULE, fetch
from .base_task import BaseTask


DOCKER_SOURCES_LIST = """\
deb [arch=amd64] https://download.docker.com/linux/{{ distro }} {{ suite }} stable
"""

DOCKER_SERVICE_OVERRIDE = """\
[Service]
ExecStart=
ExecStart=/usr/bin/dockerd -H fd:// -H tcp://0.0.0.0:{{ tcp_port }} --containerd=/run/containerd/containerd.sock
"""


class DockerTask(BaseTask):
    @staticmethod
    def task_name():
        return "docker"

    @staticmethod
    def schema():
        return {"tcp-port": {"anyof": [BOOLEAN_RULE, POSITIVE_INTEGER_RULE]}, "compose": BOOLEAN_RULE}

    def system_check(self):
        pass

    def needs_chroot(self):
        return True

    def run(self):
        tcp_port = self.config["tcp-port"]
        compose = self.config["compose"]
        compose_program = self.ctx.execution.chroot_path("/usr/local/bin/docker-compose")
        service_override_dir = "/etc/systemd/system/docker.service.d"
        service_override_dir_chroot = self.ctx.execution.chroot_path(service_override_dir)
        distro = "debian"
        suite = "buster"

        self.ctx.debian.apt_install("gnupg", "ca-certificates")

        if not self.ctx.debian.apt_is_installed("docker-ce"):
            self.ctx.shell.execute_chroot("apt-key", "add", "-", input=fetch("https://download.docker.com/linux/{}/gpg".format(distro)))
            self.ctx.template.render_to_file(DOCKER_SOURCES_LIST, "/etc/apt/sources.list.d/docker.list", distro=distro, suite=suite)
            self.ctx.debian.apt_update_packages_lists()

        self.ctx.debian.apt_install("docker-ce")

        if not tcp_port:
            self.ctx.log.debug("Disabling remote API for dockerd")
            shutil.rmtree(service_override_dir_chroot, ignore_errors=True)
        else:
            if isinstance(tcp_port, bool):
                tcp_port = 2375

            self.ctx.log.debug("Enabling remote API for dockerd on port {}".format(tcp_port))
            os.makedirs(service_override_dir_chroot, exist_ok=True)
            self.ctx.template.render_to_file(
                DOCKER_SERVICE_OVERRIDE, os.path.join(service_override_dir, "override.conf"), tcp_port=tcp_port
            )

        if compose:
            if not os.path.isfile(compose_program):
                self.ctx.log.debug("Installing docker-compose")
                fetch("https://github.com/docker/compose/releases/download/1.25.5/docker-compose-Linux-x86_64", save_file=compose_program)
                self.ctx.shell.execute("chmod", "a+x", compose_program)
        else:
            self.ctx.log.debug("Removing docker-compose")

            try:
                os.remove(compose_program)
            except:  # pylint: disable=bare-except
                pass
