import ipaddress
import os
import shutil
import xml.etree.ElementTree as ET

from ..helpers import MAC_ADDRESS_STRING_RULE, MANDATORY_STRING_RULE, POSITIVE_INTEGER_RULE
from ..contexts import ShellException
from .base_task import BaseTask, TaskException


class LibvirtTask(BaseTask):
    @staticmethod
    def task_name():
        return "libvirt"

    @staticmethod
    def schema():
        return {
            "id": POSITIVE_INTEGER_RULE,
            "name": MANDATORY_STRING_RULE,
            "pool": MANDATORY_STRING_RULE,
            "memory": {"type": "dict", "schema": {"min": POSITIVE_INTEGER_RULE, "max": POSITIVE_INTEGER_RULE}},
            "cpus": POSITIVE_INTEGER_RULE,
            "cores": POSITIVE_INTEGER_RULE,
            "network": {"type": "dict", "schema": {"mac": MAC_ADDRESS_STRING_RULE}},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.vmid = self.config["id"]
        self.name = self.config["name"]
        self.pool = self.config["pool"]
        self.min_memory = self.config["memory"]["min"]
        self.max_memory = self.config["memory"]["max"]
        self.cpus = self.config["cpus"]
        self.cores = self.config["cores"]
        self.mac = self.config["network"]["mac"]
        self.bridge = None

        self.hdd_dir = "/var/lib/libvirt/images"
        self.hdd_file = os.path.join(self.hdd_dir, "hdd-{0}-vm{2}".format("debian", *os.path.splitext("nuno.qcow")))

    def system_check(self):
        self.ctx.shell.require_programs("virsh")
        self.ctx.shell.require_programs("virt-install")

        try:
            virsh_network = "default"
            default_network_xml = self.ctx.shell.execute("virsh", "net-dumpxml", virsh_network, capture_stderr=True, capture=True)
        except ShellException as error:
            message = error.message()
            if "socket" in message:
                raise TaskException(
                    "Failed to connect virsh socket. Maybe package 'libvirt-daemon-system' is missing or 'libvirtd.service' is stopped"
                )
            if "'{}'".format(virsh_network) in message:
                raise TaskException("Failed to get network '{}' from virsh".format(virsh_network))

            raise TaskException(message)

        default_network = ET.fromstring(default_network_xml)
        self.bridge = default_network.find("bridge[@name]").attrib["name"]
        network_settings = default_network.find("ip[@address][@netmask]")
        gateway = network_settings.attrib["address"]
        netmask = network_settings.attrib["netmask"]
        hosts = [h.compressed for h in ipaddress.IPv4Network(gateway + "/" + netmask, strict=False).hosts() if h.compressed != gateway]
        self.ctx.log.message(
            os.linesep.join(
                [
                    "Using bridge interface '{}'. Make sure the VM is configured to use DHCP or the following IPv4 settings:".format(
                        self.bridge
                    ),
                    "Address: {} - {}".format(hosts[0], hosts[-1]),
                    "Netmask: " + netmask,
                    "Gatway: " + gateway,
                ]
            )
        )

        if os.path.exists(self.hdd_file):
            raise TaskException("Hdd '{}' exists".format(self.hdd_file))

    def needs_chroot(self):
        return False

    def run(self):
        self.ctx.log.debug("Iporting '{}' to '{}' pool", self.hdd_file, self.hdd_dir)
        shutil.copyfile(self.ctx.global_config.hdd_file, self.hdd_file)

        self.ctx.log.debug(
            "Creating VM '{}' with {}x{} cores, {}Mb ({}Mb max) RAM, address {} ({})",
            self.name,
            self.cpus,
            self.cores,
            self.min_memory,
            self.max_memory,
            self.mac,
            self.bridge,
        )
