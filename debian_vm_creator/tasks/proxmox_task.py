from ..helpers import MANDATORY_STRING_RULE, POSITIVE_INTEGER_RULE, MAC_ADDRESS_STRING_RULE
from .base_task import BaseTask


class ProxmoxTask(BaseTask):
    @staticmethod
    def name():
        return "proxmox"

    @staticmethod
    def schema():
        return {
            "id": POSITIVE_INTEGER_RULE,
            "description": MANDATORY_STRING_RULE,
            "pool": MANDATORY_STRING_RULE,
            "memory": {"type": "dict", "schema": {"min": POSITIVE_INTEGER_RULE, "max": POSITIVE_INTEGER_RULE}},
            "cpus": POSITIVE_INTEGER_RULE,
            "cores": POSITIVE_INTEGER_RULE,
            "network": {"type": "dict", "schema": {"mac": MAC_ADDRESS_STRING_RULE, "bridge": MANDATORY_STRING_RULE}},
        }

    def system_check(self):
        self.ctx.shell.require_programs("qm")

    def needs_chroot(self):
        return False

    def run(self):
        vmid = self.config["id"]
        description = self.config["description"]
        pool = self.config["pool"]
        min_memory = self.config["memory"]["min"]
        max_memory = self.config["memory"]["max"]
        cpus = self.config["cpus"]
        cores = self.config["cores"]
        mac = self.config["network"]["mac"]
        bridge = self.config["network"]["bridge"]
        full_name = "{} ({})".format(vmid, description)
        hdd_file = self.ctx.global_config.hdd_file
        hdd_name = "{}:vm-{}-disk-0".format(pool, vmid)

        self.ctx.log.debug(
            "Creating VM {} with {}x{} cores, {}Mb ({}Mb max) RAM, address {} ({})",
            full_name,
            cpus,
            cores,
            min_memory,
            max_memory,
            mac,
            bridge,
        )

        qm_args = ["qm", "create", str(vmid), "--name", description, "--machine", "q35", "--ostype", "l26"]
        qm_args.extend(["--balloon", str(min_memory), "--memory", str(max_memory)])
        qm_args.extend(["--cpu", "host,flags=+aes", "--sockets", str(cpus), "--cores", str(cores)])
        qm_args.extend(["--scsihw", "virtio-scsi-pci", "--net0", "virtio={},bridge={}".format(mac, bridge)])
        qm_args.extend(["--agent", "1", "--boot", "c", "--bootdisk", "scsi0"])
        qm_args.extend(["--serial0", "socket", "--vga", "serial0"])
        self.ctx.shell.execute(*qm_args)

        self.ctx.log.debug("Iporting '{}' to {} pool", hdd_file, pool)
        self.ctx.shell.execute("qm", "importdisk", str(vmid), hdd_file, pool)

        self.ctx.log.debug("Adding hdd '{}' to VM {}", hdd_name, full_name)
        self.ctx.shell.execute("qm", "set", str(vmid), "--scsi0", hdd_name)
