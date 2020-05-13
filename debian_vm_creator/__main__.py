# import logging
# import sys
# import tempfile

import logging
import sys

import click

from .helpers import YAML_FILE

# from debian_vm_creator.sh import BinaryNotFoundException, binaries_search, execute, execute_chroot
from .vm_builder import BuildException, VmBuilder


# logging.basicConfig()
# logging.getLogger().setLevel(logging.DEBUG)

# from debian_vm_creator.commands import (
#     apt_install,
#     apt_setup,
#     debootstrap,
#     device_get_partitions,
#     fstab_setup,
#     grub_setup,
#     hostname_setup,
#     keyboard_setup,
#     locales_setup,
#     mount,
#     mount_chroot,
#     nbd_connect,
#     password_setup,
#     timezone_setup,
# )
# from debian_vm_creator.console import perror, pmessage, perror_exit


# def hdd_customize(hdd, hostname, domain, root_password, address, netmask, gateway, dns, dns_search):
#     """Customizes a qcow2 virtual hdd"""

#     print(address, netmask, gateway, dns, dns_search)
#     sys.exit(0)
#     try:
#         binaries_search("ln", "lsblk", "modprobe", "mount", "qemu-nbd", "umount")
#     except BinaryNotFoundException as exception:
#         perror(str(exception))
#         sys.exit(1000)

#     with tempfile.TemporaryDirectory(prefix="debian-vm-creator-") as root_mount, nbd_connect(hdd) as nbd_dev:
#         root_dev = device_get_partitions(nbd_dev)[0]

#         with mount(root_dev, root_mount), mount_chroot(root_mount):
#             timezone_setup(root_mount, "Europe/Lisbon")
#             keyboard_setup(root_mount, "pc105", "pt")
#             hostname_setup(root_mount, hostname, domain)
#             password_setup(root_mount, root_password)


# def hdd_chroot(hdd):
#     """Chroots into a qcow2 virtual hdd"""

#     try:
#         binaries_search("lsblk", "modprobe", "mount", "qemu-nbd", "umount")
#     except BinaryNotFoundException as exception:
#         perror(str(exception))
#         sys.exit(1000)

#     with tempfile.TemporaryDirectory(prefix="debian-vm-creator-") as root_mount, nbd_connect(hdd) as nbd_dev:
#         root_dev = device_get_partitions(nbd_dev)[0]

#         with mount(root_dev, root_mount), mount_chroot(root_mount):
#             execute_chroot(root_mount, "bash", check=False)


# def vm_create(hdd, vmid, name, memory, memory_min, cpus, cores, net_bridge, mac_address, hdd_pool):
#     """Creates a kvm VM with the given qcow2 virtual hdd (Proxmox only)"""

#     try:
#         binaries_search("qm")
#     except BinaryNotFoundException as exception:
#         perror(str(exception))
#         sys.exit(1000)

#     full_name = "{} ({})".format(vmid, name)

#     pmessage("creating VM {} with {}x{} cores, {}Mb ({}Mb min) RAM, address {}", full_name, cpus, cores, memory, memory_min, mac_address)
#     qm_args = ["qm", "create", str(vmid), "--name", name, "--machine", "q35", "--ostype", "l26"]
#     qm_args.extend(["--memory", str(memory), "--balloon", str(memory_min)])
#     qm_args.extend(["--cpu", "host,flags=+aes", "--sockets", str(cpus), "--cores", str(cores)])
#     qm_args.extend(["--scsihw", "virtio-scsi-pci", "--net0", "virtio={},bridge={}".format(mac_address, net_bridge)])
#     qm_args.extend(["--agent", "1", "--boot", "c", "--bootdisk", "scsi0"])
#     execute(*qm_args)

#     pmessage("importing '{}' to {} pool", hdd, hdd_pool)
#     execute("qm", "importdisk", str(vmid), hdd, hdd_pool)

#     hdd_name = "{}:vm-{}-disk-0".format(hdd_pool, vmid)

#     pmessage("adding hdd '{}' to VM {}", hdd_name, full_name)
#     execute("qm", "set", str(vmid), "--scsi0", hdd_name)


def vm_create(vm_file):
    try:
        VmBuilder(vm_file).build()
    except BuildException:
        sys.exit(1)


def main():
    command = click.Command("vm_create", callback=vm_create)
    command.help = "A tool to create debian based VMs for Proxmox"
    command.params.append(click.Argument(["vm-file"], type=YAML_FILE))
    command(prog_name="debian-vm-creator")


if __name__ == "__main__":
    main()
