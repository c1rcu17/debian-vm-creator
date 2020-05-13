from ..helpers import DOMAIN_STRING_RULE, MANDATORY_STRING_RULE
from .base_task import BaseTask


HOSTNAME = """\
{{ hostname }}
"""

HOSTS = """\
127.0.0.1	localhost
127.0.1.1	{{ hostname }}.{{ domain }} {{ hostname }}
::1		localhost ip6-localhost ip6-loopback
ff02::1		ip6-allnodes
ff02::2		ip6-allrouters
"""


class HostnameTask(BaseTask):
    @staticmethod
    def name():
        return "hostname"

    @staticmethod
    def schema():
        return {"hostname": MANDATORY_STRING_RULE, "domain": DOMAIN_STRING_RULE}

    def system_check(self):
        pass

    def needs_chroot(self):
        return True

    def run(self):
        hostname = self.config["hostname"]
        domain = self.config["domain"]

        self.ctx.log.debug("Setting host to {}.{}", hostname, domain)
        self.ctx.template.render_to_file(HOSTNAME, "/etc/hostname", hostname=hostname)
        self.ctx.template.render_to_file(HOSTS, "/etc/hosts", hostname=hostname, domain=domain)
