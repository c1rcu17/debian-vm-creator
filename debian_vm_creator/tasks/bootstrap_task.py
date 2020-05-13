import os

from ..helpers import POSITIVE_INTEGER_RULE, URL_STRING_RULE
from .base_task import BaseTask, TaskException


FSTAB_TEMPLATE = """\
{{ '%-41s'|format('# <file system>  ') }} {{ '%-13s'|format('<mount point>') }} {{ '%-6s'|format('<type>') }} {{ '%-17s'|format('<options>') }} {{ '%-6s'|format('<dump>') }}  {{ '%-6s'|format('<pass>') }}
{{ '%-41s'|format('UUID=' + root_uuid) }} {{ '%-13s'|format('/') }} {{ '%-6s'|format('ext4') }} {{ '%-17s'|format('errors=remount-ro') }} {{ '%-6s'|format('0') }}  {{ '%-6s'|format('1') }}
"""

SOURCES_TEMPLATE = """\
deb {{ mirror }} {{ suite }} main contrib non-free
deb {{ mirror }} {{ suite }}-updates main contrib non-free
# deb {{ mirror }} {{ suite }}-backports main contrib non-free
deb http://security.debian.org/debian-security/ {{ suite }}/updates main contrib non-free
"""

GRUB_TEMPLATE = """\
GRUB_DEFAULT=0
GRUB_TIMEOUT=0
GRUB_DISTRIBUTOR=`lsb_release -i -s 2> /dev/null || echo Debian`
GRUB_CMDLINE_LINUX_DEFAULT=""
GRUB_CMDLINE_LINUX="net.ifnames=0 biosdevname=0 console=ttyS0"
GRUB_DISABLE_RECOVERY="true"
GRUB_DISABLE_OS_PROBER="true"
"""


class HddStrategy:  # pylint: disable=too-few-public-methods
    replace = "replace"
    reuse = "reuse"
    stop = "stop"

    @classmethod
    def values(cls):
        return [cls.replace, cls.reuse, cls.stop]


class BootstrapTask(BaseTask):
    @staticmethod
    def name():
        return "bootstrap"

    @staticmethod
    def schema():
        return {
            "hdd-size": POSITIVE_INTEGER_RULE,
            "hdd-strategy": {"type": "string", "allowed": HddStrategy.values()},
            "suite": {"type": "string", "allowed": ["buster"]},
            "mirror": URL_STRING_RULE,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hdd = self.ctx.global_config.hdd_file
        self.size = self.config["hdd-size"]
        self.strategy = self.config["hdd-strategy"]
        self.suite = self.config["suite"]
        self.mirror = self.config["mirror"]

    def system_check(self):
        self.ctx.shell.require_programs(
            "blkid", "debootstrap", "lsblk", "mkfs.ext4", "modprobe", "mount", "parted", "qemu-img", "qemu-nbd", "umount"
        )

    def needs_chroot(self):
        return False

    def run(self):
        if self.create_hdd():
            with self.ctx.execution.new_workdir():
                with self.ctx.execution.nbd_connect():
                    self.partition()
                    with self.ctx.execution.nbd_partition_scan():
                        self.format()
                        with self.ctx.execution.nbd_partition_mount():
                            self.debootstrap()
                            with self.ctx.execution.chroot_mount():
                                with self.ctx.execution.nbd_partition_uuid_scan():
                                    self.fstab()
                                    self.apt()
                                    self.base_packages()

                with self.ctx.execution.chroot_mount():
                    self.grub()

    def create_hdd(self):
        if os.path.exists(self.hdd):
            if self.strategy == HddStrategy.stop:
                raise TaskException("Hdd '{}' exists".format(self.hdd))

            if self.strategy == HddStrategy.reuse:
                if not os.path.isfile(self.hdd):
                    raise TaskException("File '{}' is not an Hdd".format(self.hdd))

                self.ctx.log.debug("Hdd '{}' exists, skiping bootstrap".format(self.hdd))
                return False

        self.ctx.log.debug("Creating qcow2 virtual hdd on '{}' with {}Gb", self.hdd, self.size)
        self.ctx.shell.execute("qemu-img", "create", "-f", "qcow2", self.hdd, "{}g".format(self.size))
        return True

    def partition(self):
        nbd_device = self.ctx.execution.nbd_device()

        self.ctx.log.debug("Partitioning '{}'", nbd_device)
        parted_args = ["parted", "-s", "-a", "opt", nbd_device, "--"]
        parted_args.extend(["mklabel", "msdos"])
        parted_args.extend(["mkpart", "primary", "ext4", "0%", "100%"])
        parted_args.extend(["set", "1", "boot", "on"])
        parted_args.extend(["print"])
        self.ctx.shell.execute(*parted_args)

    def format(self):
        nbd_partition = self.ctx.execution.nbd_partition()
        self.ctx.log.debug("Formatting OS root partition '{}' as ext4", nbd_partition)
        self.ctx.shell.execute("mkfs.ext4", "-L", "OS", nbd_partition)

    def debootstrap(self):
        workdir = self.ctx.execution.workdir()

        self.ctx.log.debug("Bootstrapping {} on '{}' using {}", self.suite, workdir, self.mirror)
        self.ctx.shell.execute(
            "debootstrap", "--arch=amd64", "--include=dialog", "--components=main,contrib,non-free", self.suite, workdir, self.mirror,
        )

    def fstab(self):
        nbd_partition = self.ctx.execution.nbd_partition()
        nbd_partition_uuid = self.ctx.execution.nbd_partition_uuid()

        self.ctx.log.debug("Setting fstab to use '{}' (UUID={}) as root partition", nbd_partition, nbd_partition_uuid)
        self.ctx.template.render_to_file(FSTAB_TEMPLATE, "/etc/fstab", root_uuid=nbd_partition_uuid)

    def apt(self):
        self.ctx.log.debug("Setting apt for debian {} using {}", self.suite, self.mirror)
        self.ctx.template.render_to_file(SOURCES_TEMPLATE, "/etc/apt/sources.list", suite=self.suite, mirror=self.mirror)
        self.ctx.debian.apt_update_packages_lists()
        self.ctx.shell.execute_chroot("apt-get", "-y", "dist-upgrade", environment={"DEBIAN_FRONTEND": "noninteractive"})

    def base_packages(self):
        self.ctx.debian.apt_install("linux-image-amd64", "qemu-guest-agent", no_locale=True)
        # "ca-certificates",
        # "apt-transport-https",
        # "curl",
        # "gnupg-agent",
        # # "software-properties-common",
        # "openssh-server"

    def grub(self):
        nbd_device = self.ctx.execution.nbd_device()

        self.ctx.debian.apt_install("grub2", show_dialogs=False, no_locale=True)
        self.ctx.log.debug("Setting up grub on '{}'", nbd_device)
        self.ctx.template.render_to_file(GRUB_TEMPLATE, "/etc/default/grub")
        self.ctx.shell.execute_chroot("update-grub")
        self.ctx.shell.execute_chroot("grub-install", nbd_device)
