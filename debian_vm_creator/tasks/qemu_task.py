from .base_task import BaseTask


class QemuTask(BaseTask):
    @staticmethod
    def name():
        return "quemu"

    @staticmethod
    def schema():
        return {}

    def system_check(self):
        self.ctx.shell.require_programs("libvirtd")
        # libvirt-daemon virt-viewer virtinst libvirt-clients
        # writable /var/run/libvirt/libvirt-sock

        # sudo brctl addbr br-debian-vm-cr
        ## sudo iw dev wlp1s0 set 4addr on
        # sudo iw dev wlp1s0 interface add wds.wlp1s0 type managed 4addr on
        # sudo ip link set dev wds.wlp1s0 addr 00:00:99:11:22:33
        # sudo ip link set wds.wlp1s0 up
        #
        # sudo brctl addif br-debian-vm-cr wlp1s0
        # sudo ip link set br-debian-vm-cr down
        # sudo brctl delbr br-debian-vm-cr

    def needs_chroot(self):
        return False

    def run(self):
        self.ctx.shell.execute_chroot("bash", check=False)
