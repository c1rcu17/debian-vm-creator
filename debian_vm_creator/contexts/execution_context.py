import contextlib
import json
import os
import pathlib
import tempfile

from ..helpers import AppException
from .base_context import BaseContext


class ExecutionException(AppException):
    pass


class ExecutionContext(BaseContext):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__workdir = None
        self.__nbd_loaded = False
        self.__nbd_device = None
        self.__nbd_partition = None
        self.__nbd_partition_uuid = None
        self.__mounts = []
        self.__resolvconf = None

    def workdir(self):
        if self.__workdir is None:
            raise ExecutionException("Workdir not created")
        return self.__workdir

    def nbd_device(self):
        if self.__nbd_device is None:
            raise ExecutionException("Hdd '{}' not connected".format(self.ctx.global_config.hdd_file))
        return self.__nbd_device

    def nbd_partition(self):
        if self.__nbd_partition is None:
            raise ExecutionException("Partition not scanned")
        return self.__nbd_partition

    def nbd_partition_uuid(self):
        if self.__nbd_partition_uuid is None:
            raise ExecutionException("Partition UUID not scanned")
        return self.__nbd_partition_uuid

    def chroot_path(self, path, *, follow_symlinks=False, create=False):
        if follow_symlinks:
            path = self.ctx.shell.execute_chroot("readlink", "-fn", path, capture=True)

        path_in_chroot = os.path.normpath(self.workdir() + os.path.normpath("///" + path))

        if create and not os.path.exists(path_in_chroot):
            pathlib.Path(path_in_chroot).touch()

        return path_in_chroot

    @contextlib.contextmanager
    def new_workdir(self):
        if self.__workdir is not None:
            yield
        else:
            with tempfile.TemporaryDirectory(prefix="debian-vm-creator-") as workdir:
                self.ctx.log.debug("Created workdir '{}'".format(workdir))
                self.__workdir = workdir

                try:
                    yield
                finally:
                    self.ctx.log.debug("Deleting workdir '{}'".format(workdir))
                    self.__workdir = None

    @contextlib.contextmanager
    def nbd_load_module(self):
        if self.__nbd_loaded:
            yield
        else:
            self.ctx.log.debug("Checking nbd kernel module")
            self.__nbd_loaded = not self.ctx.shell.execute("modprobe", "--first-time", "-n", "nbd", check=False, silent=True)

            if self.__nbd_loaded:
                yield
            else:
                self.ctx.log.debug("Loading nbd kernel module")
                self.ctx.shell.execute("modprobe", "--first-time", "nbd", "max_part=8")
                self.__nbd_loaded = True

                try:
                    yield
                finally:
                    self.ctx.log.debug("Unloading nbd kernel module")
                    self.ctx.shell.execute("modprobe", "-r", "--first-time", "nbd")
                    self.__nbd_loaded = False

    @contextlib.contextmanager
    def nbd_connect(self):
        if self.__nbd_device is not None:
            yield
        else:
            with self.nbd_load_module():
                hdd_file = self.ctx.global_config.hdd_file
                nbd_device = None

                for i in range(8):
                    with open("/sys/class/block/nbd{}/size".format(i), "r") as nbd_fp:
                        size = nbd_fp.read().strip()
                        if size == "0":
                            nbd_device = "/dev/nbd{}".format(i)
                            break

                self.ctx.log.debug("Connecting '{}' to '{}'", nbd_device, hdd_file)
                self.ctx.shell.execute("qemu-nbd", "--connect", nbd_device, hdd_file)
                self.__nbd_device = nbd_device

                try:
                    yield
                finally:
                    self.ctx.log.debug("Disconnecting '{}' from '{}'", nbd_device, hdd_file)
                    self.ctx.shell.execute("qemu-nbd", "--disconnect", nbd_device, silent=True)
                    self.__nbd_device = None

    @contextlib.contextmanager
    def nbd_partition_scan(self):
        if self.__nbd_partition is not None:
            yield
        else:
            with self.nbd_connect():
                ndb_dev = self.nbd_device()
                partition_index = 0

                self.ctx.log.debug("Scanning '{}' partition {}", ndb_dev, partition_index)
                blktree = json.loads(self.ctx.shell.execute("lsblk", "-JnpO", ndb_dev, capture=True))
                # TODO: clean this debug
                self.ctx.log.debug("{}", json.dumps(blktree))
                partition = blktree["blockdevices"][0]["children"][partition_index]["kname"]
                self.ctx.log.debug("Found partition '{}'", partition)
                self.__nbd_partition = partition

                try:
                    yield
                finally:
                    self.ctx.log.debug("Disposing partition '{}'", partition)
                    self.__nbd_partition = None

    @contextlib.contextmanager
    def nbd_partition_uuid_scan(self):
        if self.__nbd_partition_uuid is not None:
            yield
        else:
            with self.nbd_partition_scan():
                ndb_partition = self.nbd_partition()

                self.ctx.log.debug("Scanning '{}' UUID", ndb_partition)
                uuid = self.ctx.shell.execute("blkid", "-s", "UUID", "-o", "value", ndb_partition, capture=True)

                if not uuid:
                    raise ExecutionException("Partition UUID not found")

                self.ctx.log.debug("Found UUID '{}'", uuid)
                self.__nbd_partition_uuid = uuid

                try:
                    yield
                finally:
                    self.ctx.log.debug("Disposing UUID '{}'", uuid)
                    self.__nbd_partition_uuid = None

    @contextlib.contextmanager
    def nbd_partition_mount(self):
        with self.nbd_partition_scan(), self.__mount("auto", self.nbd_partition(), "/"):
            yield

    @contextlib.contextmanager
    def proc_mount(self):
        with self.nbd_partition_mount(), self.__mount("proc", "proc", "/proc"):
            yield

    @contextlib.contextmanager
    def sys_mount(self):
        with self.nbd_partition_mount(), self.__mount("sysfs", "sys", "/sys"):
            yield

    @contextlib.contextmanager
    def dev_mount(self):
        with self.nbd_partition_mount(), self.__mount("auto", "/dev", "/dev", options=["bind"]):
            yield

    @contextlib.contextmanager
    def dev_pts_mount(self):
        with self.dev_mount(), self.__mount("auto", "/dev/pts", "/dev/pts", options=["bind"]):
            yield

    @contextlib.contextmanager
    def temp_resolvconf(self):
        if self.__resolvconf is not None:
            yield
        else:
            with self.new_workdir():
                resolv_file = self.chroot_path("/etc/resolv.conf", follow_symlinks=True, create=True)
                self.ctx.log.debug("Backing up '{}'", resolv_file)

                with open(resolv_file, "r+") as stream:
                    self.__resolvconf = stream.read()
                    stream.seek(0)
                    stream.writelines("nameserver {}\n".format(n) for n in ["1.1.1.1", "8.8.8.8", "8.8.4.4"])
                    stream.truncate()

                try:
                    yield
                finally:
                    resolv_file = self.chroot_path("/etc/resolv.conf", follow_symlinks=True, create=True)
                    self.ctx.log.debug("Restoring '{}'", resolv_file)

                    with open(resolv_file, "w") as stream:
                        stream.write(self.__resolvconf)

                    self.__resolvconf = None

    @contextlib.contextmanager
    def chroot_mount(self):
        with self.proc_mount(), self.sys_mount(), self.dev_pts_mount(), self.temp_resolvconf():
            yield

    @contextlib.contextmanager
    def __mount(self, filesystem, source, directory, options=None):
        directory = os.path.normpath("///" + directory)

        if directory in self.__mounts:
            yield
        else:
            with self.new_workdir():
                target = os.path.normpath(self.workdir() + directory)

                self.ctx.log.debug("Mounting '{}' with {} filesystem on '{}'", source, filesystem, target)
                mount_args = ["mount", "-t", filesystem]

                if options:
                    mount_args.extend(["-o", ",".join(options)])

                mount_args.extend([source, target])
                self.ctx.shell.execute(*mount_args)
                self.__mounts.append(directory)

                try:
                    yield
                finally:
                    self.ctx.log.debug("Unmounting '{}'", target)
                    self.ctx.shell.execute("umount", target)
                    self.__mounts.pop()
