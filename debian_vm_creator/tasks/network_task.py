import ipaddress

from ..helpers import DOMAIN_STRING_RULE, IPV4_STRING_RULE
from .base_task import BaseTask


ETH0 = """\
auto eth0
iface eth0 inet static
    address {{ address }}
    netmask {{ netmask }}
    network {{ network }}
    broadcast {{ broadcast }}
    gateway {{ gateway }}
    {% for host in dns_hosts %}dns-nameserver {{ host }}
    {% endfor %}dns-search{% for search in dns_search %} {{ search }}{% endfor %}
"""


class NetworkTask(BaseTask):
    @staticmethod
    def name():
        return "network"

    @staticmethod
    def schema():
        return {
            "address": IPV4_STRING_RULE,
            "netmask": IPV4_STRING_RULE,
            "gateway": IPV4_STRING_RULE,
            "dns": {
                "type": "dict",
                "schema": {
                    "hosts": {"schema": IPV4_STRING_RULE, "type": "list"},
                    "search": {"schema": DOMAIN_STRING_RULE, "type": "list"},
                },
            },
        }

    def system_check(self):
        pass

    def needs_chroot(self):
        return True

    def run(self):
        address = self.config["address"]
        netmask = self.config["netmask"]
        gateway = self.config["gateway"]
        dns_hosts = self.config["dns"]["hosts"]
        dns_search = self.config["dns"]["search"]
        ipv4_network = ipaddress.IPv4Network("{}/{}".format(address, netmask), strict=False)
        network = ipv4_network.network_address
        broadcast = ipv4_network.broadcast_address

        self.ctx.debian.apt_install("resolvconf")
        self.ctx.log.debug("Setting up eth0 with static ip '{}' nm '{}' gw '{}'", address, netmask, gateway)
        self.ctx.template.render_to_file(
            ETH0,
            "/etc/network/interfaces.d/eth0",
            address=address,
            netmask=netmask,
            gateway=gateway,
            dns_hosts=dns_hosts,
            dns_search=dns_search,
            network=network,
            broadcast=broadcast,
        )
