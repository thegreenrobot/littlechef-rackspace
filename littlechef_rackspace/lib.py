import os
import sys
from libcloud.compute.base import NodeImage, NodeSize
from libcloud.compute.providers import get_driver
from libcloud.compute.types import Provider, NodeState
import time
from options import parser
from littlechef import runner as lc

def raise_error(text):
    print("Error: %s" % text)
    parser.print_help()
    sys.exit(1)

def get_provider(options):
    region = options.region.lower()

    if region == "dfw":
        return Provider.RACKSPACE_NOVA_DFW
    if region == "ord":
        return Provider.RACKSPACE_NOVA_ORD

    raise_error("must specify region (DFW or ORD)")

def get_conn(options):
    RACKSPACE_USER = options.username or os.environ.get("RACKSPACE_USER")
    RACKSPACE_APIKEY = options.apikey or os.environ.get("RACKSPACE_APIKEY")

    if not RACKSPACE_USER:
        raise_error("RACKSPACE_USER not set!")
    if not RACKSPACE_APIKEY:
        raise_error("RACKSPACE_APIKEY not set!")

    Driver = get_driver(get_provider(options))
    return Driver(RACKSPACE_USER, RACKSPACE_APIKEY,
                  ex_force_auth_url="https://identity.api.rackspacecloud.com/v2.0",
                  ex_force_auth_version="2.0")


def create_node(conn, name, image, flavor, public_key):
    image = NodeImage(id=image, name=None, driver=conn)
    flavor = NodeSize(id=flavor, name=None, ram=None, disk=None, bandwidth=None, price=None, driver=conn)

    sys.stderr.write("Creating node %s (image: %s, flavor: %s)...\n" % (name, image.id, flavor.id))

    return conn.create_node(name=name, image=image, size=flavor, ex_files={
        "/root/.ssh/authorized_keys": public_key
    })

def _get_ipv4_address(node):
    # Dumb hack to not ssh into the ipv6 address
    return [ip for ip in node.public_ips if ":" not in ip][0]

def deploy_chef(options, host):
    ipv4_address = host.host_string
    sys.stderr.write("Deploying Chef on host %s...\n" % ipv4_address)

    lc.env.user = "root"
    lc.env.key_filename = options.private_key
    lc.env.host_string = ipv4_address
    lc.env.host = ipv4_address
    lc.deploy_chef(ask="no")


def save_node(options, host):
    lc.env.user = "root"
    lc.env.key_filename = options.private_key

    roles = options.roles.split(',')
    if roles:
        # TODO use littlechef lib /chef modules directly to avoid
        # running chef multiple times here
        for role in roles:
            lc.role(role)
    else:
        lc.node(host.host_string)

    # TODO: rename file and yell about setting up DNS I guess


class Host(object):

    """
    Internal representation of a newly created/rebuilt server
    for Chef deployment, role addition, etc.
    """

    def __init__(self, name=None, host_string=None, password=None):
        self.name = name
        self.host_string = host_string
        self.password = password

    def __repr__(self):
        return '<Host name={0}, host_string={1}, password={2}>'.format(
            self.name, self.host_string, self.password
        )

    def __eq__(self, other):
        return (self.name == other.name and
                self.host_string == other.host_string and
                self.password == other.password)