from StringIO import StringIO
import unittest
import mock
import sys
from littlechef_rackspace.api import RackspaceApi
from littlechef_rackspace.commands import RackspaceCreate
from littlechef_rackspace.deploy import ChefDeployer
from littlechef_rackspace.lib import Host

class RackspaceCreateTest(unittest.TestCase):

    def setUp(self):
        self.api = mock.Mock(spec=RackspaceApi)
        self.deployer = mock.Mock(spec=ChefDeployer)
        self.command = RackspaceCreate(rackspace_api=self.api,
                                       chef_deployer=self.deployer)
        self.host = Host()
        self.api.create_node.return_value = self.host

    def test_creates_host_in_api(self):
        node_name = "test"
        image_id = "imageId"
        flavor_id = "flavorId"
        public_key_file = StringIO("~/.ssh/id_rsa.pub")

        self.command.execute(node_name=node_name, image_id=image_id,
                             flavor_id=flavor_id, public_key_file=public_key_file)

        self.api.create_node.assert_any_call(node_name=node_name, image_id=image_id,
                                             flavor_id=flavor_id, public_key_file=public_key_file,
                                             progress=sys.stderr)

    def test_deploys_to_host_without_runlist(self):
        self.command.execute(node_name="something", image_id="imageId",
                             flavor_id="fileId", public_key_file=StringIO("whatever"))

        self.deployer.deploy.assert_any_call(host=self.host, runlist=[])

    def test_deploys_to_host_with_runlist(self):
        runlist = ["role[web]", "recipe[test]"]
        self.command.execute(node_name="something", image_id="imageId",
                             flavor_id="fileId", public_key_file=StringIO("whatever"),
                             runlist=runlist)

        self.deployer.deploy.assert_any_call(host=self.host, runlist=runlist)
