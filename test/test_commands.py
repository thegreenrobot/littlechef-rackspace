from StringIO import StringIO
import unittest
import mock
import sys
from littlechef_rackspace.api import RackspaceApi
from littlechef_rackspace.commands import RackspaceCreate, RackspaceListImages, RackspaceListFlavors
from littlechef_rackspace.deploy import ChefDeployer
from littlechef_rackspace.lib import Host

class RackspaceCreateTest(unittest.TestCase):

    def setUp(self):
        self.api = mock.Mock(spec=RackspaceApi)
        self.deployer = mock.Mock(spec=ChefDeployer)
        self.command = RackspaceCreate(rackspace_api=self.api,
                                       chef_deployer=self.deployer)
        self.api.create_node.return_value = Host()

    def test_creates_host_in_api(self):
        node_name = "test"
        image = "imageId"
        flavor = "flavorId"
        public_key_file = StringIO("~/.ssh/id_rsa.pub")

        self.command.execute(node_name=node_name, image=image,
                             flavor=flavor, public_key_file=public_key_file)

        self.api.create_node.assert_any_call(node_name=node_name, image=image,
                                             flavor=flavor, public_key_file=public_key_file,
                                             progress=sys.stderr)

    def test_deploys_to_host_without_runlist(self):
        self.command.execute(node_name="something", image="imageId",
                             flavor="fileId", public_key_file=StringIO("whatever"))

        self.deployer.deploy.assert_any_call(host=Host(), runlist=None, plugins=None,
                                             post_plugins=None)

    def test_deploys_to_host_with_hostname(self):
        self.command.execute(node_name="something", image="imageId",
                             flavor="fileId", public_key_file=StringIO("whatever"),
                             hostname="test.example.com")

        self.deployer.deploy.assert_any_call(host=Host(host_string="test.example.com"),
                                             runlist=None, plugins=None,
                                             post_plugins=None)

    def test_deploys_to_host_with_environment(self):
        self.command.execute(node_name="something", image="imageId",
                             flavor="fileId", public_key_file=StringIO("whatever"),
                             environment='staging')

        expected_host = Host()
        expected_host.environment = 'staging'

        self.deployer.deploy.assert_any_call(host=expected_host,
                                             runlist=None, plugins=None,
                                             post_plugins=None)

    def test_deploys_to_host_with_runlist_and_plugins(self):
        runlist = ["role[web]", "recipe[test]"]
        plugins = ['plugin1', 'plugin2', 'plugin3']

        self.command.execute(node_name="something", image="imageId",
                             flavor="fileId", public_key_file=StringIO("whatever"),
                             runlist=runlist, plugins=plugins)

        self.deployer.deploy.assert_any_call(host=Host(),
                                             runlist=runlist, plugins=plugins,
                                             post_plugins=None)

    def test_deploys_to_host_with_post_plugins(self):
        post_plugins = ['plugin1', 'plugin2', 'plugin3']

        self.command.execute(node_name="something", image="imageId",
                             flavor="fileId", public_key_file=StringIO("whatever"),
                             post_plugins=post_plugins)

        self.deployer.deploy.assert_any_call(host=Host(),
                                             runlist=None, plugins=None,
                                             post_plugins=post_plugins)

class RackspaceListImagesTest(unittest.TestCase):

    def setUp(self):
        self.api = mock.Mock(spec=RackspaceApi)
        self.command = RackspaceListImages(rackspace_api=self.api)

    def test_outputs_images(self):
        progress = StringIO()
        image1 = {'id': '1', 'name': 'Ubuntu 12.04 LTS'}
        image2 = {'id': '2', 'name': 'Ubuntu 10.04 LTS'}
        self.api.list_images.return_value = [ image1, image2 ]

        self.command.execute(progress=progress)

        self.assertEquals([
                              '{0}{1}'.format(image1['id'].ljust(38 + 5), image1['name']),
                              '{0}{1}'.format(image2['id'].ljust(38 + 5), image2['name'])
                          ], progress.getvalue().splitlines())

class RackspaceListFlavorsTest(unittest.TestCase):

    def setUp(self):
        self.api = mock.Mock(spec=RackspaceApi)
        self.command = RackspaceListFlavors(rackspace_api=self.api)

    def test_outputs_flavors(self):
        progress = StringIO()
        flavor1 = {'id': '1', 'name': '256 MB'}
        flavor2 = {'id': '2', 'name': '512 MB'}
        self.api.list_flavors.return_value = [ flavor1, flavor2 ]

        self.command.execute(progress=progress)

        self.assertEquals([
                              '{0}{1}'.format(flavor1['id'].ljust(10), flavor1['name']),
                              '{0}{1}'.format(flavor2['id'].ljust(10), flavor2['name'])
                          ], progress.getvalue().splitlines())
