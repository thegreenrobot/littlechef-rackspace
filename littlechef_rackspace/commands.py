import sys

class Command(object):

    requires_api = False
    requires_deploy = False

    def __init__(self, rackspace_api=None, chef_deployer=None):
        self.rackspace_api = rackspace_api

    def execute(self, **kwargs):
        pass

class RackspaceCreate(Command):

    name = "create"
    description = "Create new Cloud Server and bootstrap Chef"
    requires_api = True
    requires_deploy = True

    def __init__(self, rackspace_api, chef_deployer):
        super(RackspaceCreate, self).__init__(rackspace_api)
        self.chef_deploy = chef_deployer

    def execute(self, node_name, flavor_id, image_id, public_key_file, runlist=[], **kwargs):
        host = self.rackspace_api.create_node(node_name=node_name, flavor_id=flavor_id,
                                              image_id=image_id, public_key_file=public_key_file,
                                              progress=sys.stderr)
        self.chef_deploy.deploy(host=host, runlist=runlist)
        # TODO: possibly rename host file based on another argument and yell about setting up DNS

class RackspaceListImages(Command):

    name = "list-images"
    description = "List available images for a Cloud Servers endpoint"
    requires_api = True

    def execute(self, **kwargs):
        self.rackspace_api.list_images(progress=sys.stderr)
