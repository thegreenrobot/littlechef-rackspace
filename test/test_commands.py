from StringIO import StringIO
import unittest2 as unittest
import mock
import sys
from littlechef_rackspace.api import RackspaceApi
from littlechef_rackspace.commands import (RackspaceCreate,
                                           RackspaceListImages,
                                           RackspaceListFlavors,
                                           RackspaceListNetworks,
                                           RackspaceListServers,
                                           RackspaceRebuild)
from littlechef_rackspace.deploy import ChefDeployer
from littlechef_rackspace.lib import Host


class RackspaceCreateTest(unittest.TestCase):

    def setUp(self):
        self.api = mock.Mock(spec=RackspaceApi)
        self.deployer = mock.Mock(spec=ChefDeployer)
        self.command = RackspaceCreate(rackspace_api=self.api,
                                       chef_deployer=self.deployer)
        self.api.create_node.return_value = Host()

    def test_dry_run_does_not_create_node_in_api(self):
        self.command.execute(name="not-importnat", image="imageId",
                             flavor="fileId",
                             public_key_file=StringIO("whatever"),
                             progress=StringIO(),
                             dry_run=True)

        self.assertEqual(len(self.api.create_node.call_args_list), 0)

    def test_create_outputs_arguments(self):
        progress = StringIO()
        self.command.execute(name="not-important", image="imageId",
                             environment='production',
                             flavor="flavorId",
                             public_key_file=StringIO("whatever"),
                             progress=progress)

        output_arguments = progress.getvalue()
        self.assertEqual(
            output_arguments.replace(' ', ''),
            """Creating node with arguments:
{
    "environment": "production",
    "flavor": "flavorId",
    "name": "not-important",
    "image": "imageId",
    "networks": null
}
""".replace(' ', '')
        )

    def test_creates_host_in_api(self):
        node_name = "test"
        image = "imageId"
        flavor = "flavorId"
        public_key_file = StringIO("~/.ssh/id_rsa.pub")

        self.command.execute(name=node_name, image=image,
                             flavor=flavor, public_key_file=public_key_file,
                             progress=StringIO())

        self.api.create_node.assert_any_call(name=node_name, image=image,
                                             flavor=flavor,
                                             public_key_file=public_key_file,
                                             networks=None,
                                             progress=sys.stderr)

    def test_deploys_to_host_with_kwargs(self):
        kwargs = {
            'runlist': ['role[web]', 'recipe[test'],
            'plugins': 'bootstrap',
            'post_plugins': 'all_done'
        }
        self.command.execute(name="something",
                             image="imageId",
                             flavor="fileId",
                             public_key_file=StringIO("whatever"),
                             progress=StringIO(),
                             **kwargs)

        expected_args = {
            'host': Host()
        }
        expected_args.update(kwargs)

        self.deployer.deploy.assert_any_call(**expected_args)

    def test_deploys_to_host_with_environment(self):
        self.command.execute(name="something", image="imageId",
                             flavor="fileId",
                             public_key_file=StringIO("whatever"),
                             progress=StringIO(),
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
        self.api.list_images.return_value = [image1, image2]

        self.command.execute(progress=progress)

        self.assertEquals([
            '{0}{1}'.format(
                image1['id'].ljust(38 + 5),
                image1['name']),
            '{0}{1}'.format(
                image2['id'].ljust(38 + 5),
                image2['name'])],
            progress.getvalue().splitlines())


class RackspaceListFlavorsTest(unittest.TestCase):

    def setUp(self):
        self.api = mock.Mock(spec=RackspaceApi)
        self.command = RackspaceListFlavors(rackspace_api=self.api)

    def test_outputs_flavors(self):
        progress = StringIO()
        flavor1 = {'id': '1', 'name': '256 MB'}
        flavor2 = {'id': '2', 'name': '512 MB'}
        self.api.list_flavors.return_value = [flavor1, flavor2]

        self.command.execute(progress=progress)

        self.assertEquals([
                          '{0}{1}'.format(
                              flavor1['id'].ljust(20),
                              flavor1['name']),
                          '{0}{1}'.format(
                              flavor2['id'].ljust(20),
                              flavor2['name'])
                          ], progress.getvalue().splitlines())


class RackspaceListNetworksTest(unittest.TestCase):

    def setUp(self):
        self.api = mock.Mock(spec=RackspaceApi)
        self.command = RackspaceListNetworks(rackspace_api=self.api)

    def test_outputs_networks(self):
        progress = StringIO()
        network1 = {
            'id': '0',
            'name': 'PublicNet',
            'cidr': None
            }
        network2 = {
            'id': '1',
            'name': 'My Test Network',
            'cidr': '192.168.0.0/20'
            }
        network3 = {
            'id': '2',
            'name': 'ServiceNet',
            'cidr': '10.0.0.0/20'
            }
        self.api.list_networks.return_value = [network1, network2, network3]

        self.command.execute(progress=progress)

        self.assertEquals([
            '{0}{1}{2}'.format(
                network1['id'].ljust(36 + 5),
                "--".ljust(20),
                network1['name']),
            '{0}{1}{2}'.format(
                network2['id'].ljust(36 + 5),
                network2['cidr'].ljust(20),
                network2['name']),
            '{0}{1}{2}'.format(
                network3['id'].ljust(36 + 5),
                network3['cidr'].ljust(20),
                network3['name'])
        ], progress.getvalue().splitlines())


class RackspaceListServersTest(unittest.TestCase):

    def setUp(self):
        self.api = mock.Mock(spec=RackspaceApi)
        self.command = RackspaceListServers(rackspace_api=self.api)

    def test_outputs_servers(self):
        progress = StringIO()
        server1 = {'id': '0', 'name': 'server1', 'public_ipv4': '50.50.50.50'}
        server2 = {'id': '1', 'name': 'server2', 'public_ipv4': '51.51.51.51'}
        self.api.list_servers.return_value = [server1, server2]

        self.command.execute(progress=progress)

        self.assertEquals([
            '{0}{1}{2}'.format(server1['id'].ljust(36 + 5),
                               server1['name'].ljust(20),
                               server1['public_ipv4']),
            '{0}{1}{2}'.format(server2['id'].ljust(36 + 5),
                               server2['name'].ljust(20),
                               server2['public_ipv4']),
        ], progress.getvalue().splitlines())


class RackspaceRebuildTest(unittest.TestCase):

    def setUp(self):
        self.api = mock.Mock(spec=RackspaceApi)
        self.deployer = mock.Mock(spec=ChefDeployer)
        self.command = RackspaceRebuild(rackspace_api=self.api,
                                        chef_deployer=self.deployer)
        self.api.rebuild_node.return_value = Host()

    def test_rebuilds_server_with_api(self):
        server_name = "awesomely named server"
        image = "imageId"
        public_key_file = StringIO("~/.ssh/id_rsa.pub")

        self.command.execute(name=server_name, image=image,
                             public_key_file=public_key_file)

        self.api.rebuild_node.assert_any_call(name=server_name,
                                              image=image,
                                              public_key_file=public_key_file,
                                              progress=sys.stderr)

    def test_deploys_to_host_with_kwargs(self):
        kwargs = {
            'runlist': ['role[web]', 'recipe[test'],
            'plugins': 'bootstrap',
            'post_plugins': 'all_done'
        }
        self.command.execute(name="something",
                             image="imageId",
                             public_key_file=StringIO("whatever"),
                             progress=StringIO(),
                             **kwargs)

        expected_args = {
            'host': Host()
        }
        expected_args.update(kwargs)

        self.deployer.deploy.assert_any_call(**expected_args)

    def test_deploys_to_host_with_environment(self):
        self.command.execute(name="something", image="imageId",
                             public_key_file=StringIO("whatever"),
                             progress=StringIO(),
                             environment='staging')

        expected_host = Host()
        expected_host.environment = 'staging'

        self.deployer.deploy.assert_any_call(host=expected_host)
