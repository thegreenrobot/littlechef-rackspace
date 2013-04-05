import sys

class Command(object):

    requires_api = False
    requires_deploy = False

    def __init__(self, rackspace_api=None, chef_deployer=None):
        self.rackspace_api = rackspace_api

    def execute(self, **kwargs):
        pass

    def validate_args(self, **kwargs):
        return True

class RackspaceCreate(Command):

    name = "create"
    description = "Create new Cloud Server and bootstrap Chef"
    requires_api = True
    requires_deploy = True

    def __init__(self, rackspace_api, chef_deployer):
        super(RackspaceCreate, self).__init__(rackspace_api)
        self.chef_deploy = chef_deployer

    def execute(self, node_name, flavor, image, public_key_file, environment=None, hostname=None, networks=None, **kwargs):
        host = self.rackspace_api.create_node(node_name=node_name, flavor=flavor,
                                              image=image, public_key_file=public_key_file,
                                              networks=networks,
                                              progress=sys.stderr)
        if environment:
            host.environment = environment
        if hostname:
            host.host_string = hostname

        self.chef_deploy.deploy(host=host, **kwargs)

    def validate_args(self, **kwargs):
        required_args = ["node_name", "flavor", "image"]
        for arg in required_args:
            if not kwargs.get(arg):
                return False

        return True

class RackspaceListImages(Command):

    name = "list-images"
    description = "List available images for a Cloud Servers endpoint"
    requires_api = True

    def execute(self, progress=sys.stderr, **kwargs):
        images = self.rackspace_api.list_images()
        for image in images:
            progress.write('{0}{1}\n'.format(image['id'].ljust(43), image['name']))

class RackspaceListFlavors(Command):

    name = "list-flavors"
    description = "List available flavors for a Cloud Servers endpoint"
    requires_api = True

    def execute(self, progress=sys.stderr, **kwargs):
        flavors = self.rackspace_api.list_flavors()
        for flavor in flavors:
            progress.write('{0}{1}\n'.format(flavor['id'].ljust(10), flavor['name']))

class RackspaceListNetworks(Command):

    name = "list-networks"
    description = "List available networks for a Cloud Servers endpoint"
    requires_api = True

    def execute(self, progress=sys.stderr, **kwargs):
        networks = self.rackspace_api.list_networks()

        for network in networks:
            cidr = network['cidr'] or '--'
            progress.write('{0}{1}{2}\n'.format(network['id'].ljust(41),
                                                cidr.ljust(20),
                                                network['name']))
