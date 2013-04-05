from StringIO import StringIO
import unittest2 as unittest
import mock
import sys
from littlechef_rackspace.api import RackspaceApi
from littlechef_rackspace.commands import RackspaceCreate, RackspaceListImages, RackspaceListFlavors, RackspaceListNetworks
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
                                             networks=None,
                                             progress=sys.stderr)

    def test_deploys_to_host_with_kwargs(self):
        kwargs = {
            'runlist': ['role[web]', 'recipe[test'],
            'plugins': 'bootstrap',
            'post_plugins': 'all_done'
        }
        self.command.execute(node_name="something", image="imageId",
                             flavor="fileId", public_key_file=StringIO("whatever"),
                             **kwargs)

        expected_args = {
            'host': Host()
        }
        expected_args.update(kwargs)

        self.deployer.deploy.assert_any_call(**expected_args)

    def test_deploys_to_host_with_hostname(self):
        self.command.execute(node_name="something", image="imageId",
                             flavor="fileId", public_key_file=StringIO("whatever"),
                             hostname="test.example.com")

        self.deployer.deploy.assert_any_call(host=Host(host_string="test.example.com"))

    def test_deploys_to_host_with_environment(self):
        self.command.execute(node_name="something", image="imageId",
                             flavor="fileId", public_key_file=StringIO("whatever"),
                             environment='staging')

        expected_host = Host()
        expected_host.environment = 'staging'

        self.deployer.deploy.assert_any_call(host=expected_host)

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


class RackspaceListNetworksTest(unittest.TestCase):

    def setUp(self):
        self.api = mock.Mock(spec=RackspaceApi)
        self.command = RackspaceListNetworks(rackspace_api=self.api)

    def test_outputs_networks(self):
        progress = StringIO()
        network1 = { 'id': '0', 'name': 'PublicNet', 'cidr': None }
        network2 = { 'id': '1', 'name': 'My Test Network', 'cidr': '192.168.0.0/20' }
        network3 = { 'id': '2', 'name': 'ServiceNet', 'cidr': '10.0.0.0/20' }
        self.api.list_networks.return_value = [ network1, network2, network3 ]

        self.command.execute(progress=progress)

        self.assertEquals([
            '{0}{1}{2}'.format(network1['id'].ljust(36 + 5), "--".ljust(20), network1['name']),
            '{0}{1}{2}'.format(network2['id'].ljust(36 + 5), network2['cidr'].ljust(20), network2['name']),
            '{0}{1}{2}'.format(network3['id'].ljust(36 + 5), network3['cidr'].ljust(20), network3['name'])
        ], progress.getvalue().splitlines())
