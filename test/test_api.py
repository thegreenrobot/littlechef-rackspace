from StringIO import StringIO
import unittest2 as unittest
from libcloud.compute.base import NodeImage, Node, NodeSize
from libcloud.compute.types import Provider, NodeState
from libcloud.compute.drivers.openstack import OpenStackNetwork

import mock
from littlechef_rackspace.api import RackspaceApi
from littlechef_rackspace.lib import Host


class RackspaceApiTest(unittest.TestCase):
    def setUp(self):
        self.username = 'username'
        self.key = 'deadbeef'

        self.pending_node = Node(
            id='id',
            name='name',
            public_ips=[],
            private_ips=[],
            state=NodeState.PENDING,
            driver=None)
        self.active_node = Node(
            id='id',
            name='name',
            public_ips=['50.2.3.4'],
            private_ips=[],
            state=NodeState.RUNNING,
            driver=None)

    def test_list_images_instantiates_driver_with_user_passwd_and_region(self):
        with mock.patch("littlechef_rackspace.api.get_driver") as get_driver:
            driver = get_driver.return_value

            api = self._get_api('dfw')
            api.list_images()

            driver.assert_any_call(self.username, self.key, region='dfw')

    def test_list_images_instantiates_dfw_driver(self):
        with mock.patch("littlechef_rackspace.api.get_driver") as get_driver:
            api = self._get_api('dfw')
            api.list_images()

        get_driver.assert_any_call(Provider.RACKSPACE)

    def _get_api_with_mocked_conn(self, conn):
        api = self._get_api('ord')
        api._get_conn = mock.Mock(return_value=conn)

        self.counter = 0

        def ex_get_node_details(id):
            if self.counter == 5:
                return self.active_node

            self.counter += 1
            return self.pending_node
        conn.ex_get_node_details.side_effect = ex_get_node_details

        return api

    def test_list_images_returns_image_information(self):
        conn = mock.Mock()
        api = self._get_api_with_mocked_conn(conn)

        lc_image1 = NodeImage('abc-def', 'Image 1', None)
        lc_image2 = NodeImage('fge-hgi', 'Image 2', None)

        conn.list_images.return_value = [lc_image1, lc_image2]

        self.assertEquals([{
            'id': lc_image1.id,
            'name': lc_image1.name
            },
            {
                'id': lc_image2.id,
                'name': lc_image2.name
            }],
            api.list_images())

    def test_list_flavors_returns_size_information(self):
        conn = mock.Mock()
        api = self._get_api_with_mocked_conn(conn)

        lc_size1 = NodeSize('1', '256 MB image', None, None, None, None, None)
        lc_size2 = NodeSize('2', '512 MB image', None, None, None, None, None)

        conn.list_sizes.return_value = [lc_size1, lc_size2]

        self.assertEquals([{
            'id': lc_size1.id,
            'name': lc_size1.name
            },
            {
                'id': lc_size2.id,
                'name': lc_size2.name
            }],
            api.list_flavors())

    def test_list_servers_returns_server_information(self):
        conn = mock.Mock()
        api = self._get_api_with_mocked_conn(conn)

        lc_node1 = Node('1', 'server1', None, ['50.50.50.50'], [], None)
        lc_node2 = Node('2', 'server2', None, ['51.51.51.51'], [], None)

        conn.list_nodes.return_value = [lc_node1, lc_node2]

        self.assertEquals([{
            'id': lc_node1.id,
            'name': lc_node1.name,
            'public_ipv4': lc_node1.public_ips[0]
        }, {
            'id': lc_node2.id,
            'name': lc_node2.name,
            'public_ipv4': lc_node2.public_ips[0]
        }], api.list_servers())

    def test_list_networks_returns_network_information(self):
        conn = mock.Mock()
        api = self._get_api_with_mocked_conn(conn)

        network1 = OpenStackNetwork(id="abcdef", cidr="192.168.0.0/16",
                                    name="awesome network",
                                    driver=None)
        conn.ex_list_networks.return_value = [network1]

        self.assertEquals([{
            'id': network1.id,
            'name': network1.name,
            'cidr': network1.cidr}],
            api.list_networks())

    def test_creates_node(self):
        conn = mock.Mock()
        api = self._get_api_with_mocked_conn(conn)

        image_id = "5cebb13a-f783-4f8c-8058-c4182c724ccd"
        flavor_id = "2"
        name = "new-node"
        public_key = "ssh-file deadbeef dave@isis"
        public_key_io = StringIO(public_key)
        conn.create_node.return_value = self.active_node

        api.create_node(name=name,
                        image=image_id,
                        flavor=flavor_id,
                        public_key_file=public_key_io)

        call_kwargs = conn.create_node.call_args_list[0][1]
        self.assertEquals(name, call_kwargs['name'])
        self.assertEquals(image_id, call_kwargs['image'].id)
        self.assertEquals(flavor_id, call_kwargs['size'].id)
        self.assertEquals({"/root/.ssh/authorized_keys": public_key},
                          call_kwargs['ex_files'])

    def test_creates_node_with_networks(self):
        conn = mock.Mock()
        api = self._get_api_with_mocked_conn(conn)
        network_id_list = ['id1', 'id2', 'id3']
        conn.create_node.return_value = self.active_node

        api.create_node(name="some name",
                        image="some image",
                        flavor="some flavor",
                        public_key_file=StringIO("some public key"),
                        networks=network_id_list)

        call_kwargs = conn.create_node.call_args_list[0][1]
        networks_kwarg = call_kwargs['networks']
        for network in networks_kwarg:
            self.assertIsInstance(network, OpenStackNetwork)

        self.assertEquals(network_id_list,
                          [network.id for network in networks_kwarg])

    def test_waits_for_node_to_become_active(self):
        conn = mock.Mock()
        api = self._get_api_with_mocked_conn(conn)

        conn.create_node.return_value = self.pending_node
        conn.ex_get_node_details.return_value = self.active_node

        with mock.patch('littlechef_rackspace.api.time') as time:
            api.create_node(name="some name",
                            image="5cebb13a-f783-4f8c-8058-c4182c724ccd",
                            flavor="2",
                            public_key_file=StringIO("some public key"))
            time.sleep.assert_any_call(5)

    def test_returns_host_information(self):
        conn = mock.Mock()
        api = self._get_api_with_mocked_conn(conn)

        public_ipv4_address = "50.51.52.53"
        self.active_node.public_ips = [
            "2222::2222:2",
            public_ipv4_address
        ]
        self.active_node.extra['password'] = 'password'
        self.active_node.name = "some name"

        conn.create_node.return_value = self.active_node

        result = api.create_node(name="some name",
                                 image="5cebb13a-f783-4f8c-8058-c4182c724ccd",
                                 flavor="2",
                                 public_key_file=StringIO("some public key"))

        self.assertEquals(result, Host(name="some name",
                                       ip_address=public_ipv4_address))

    def test_outputs_progress_during_creation(self):
        conn = mock.Mock()
        api = self._get_api_with_mocked_conn(conn)
        progress = StringIO()
        conn.create_node.return_value = self.pending_node

        password = 'abcDEFghiJKL'
        self.pending_node.extra['password'] = password

        with mock.patch('littlechef_rackspace.api.time'):
            name = "new node"
            image_id = "dontcare"
            flavor_id = "2"
            host = api.create_node(name=name,
                                   image=image_id,
                                   flavor=flavor_id,
                                   public_key_file=StringIO("some key"),
                                   progress=progress)

            self.assertEquals([
                "Creating node {0} (image: {1}, flavor: {2})...".format(
                    name,
                    image_id,
                    flavor_id),
                "Created node {0} (id: {1}, password: {2})".format(
                    name,
                    self.pending_node.id,
                    password),
                "Waiting for node to become active{0}".format("." * 6),
                "Node active! (host: {0})".format(host.ip_address)
            ], progress.getvalue().splitlines())

    def test_rebuild_node(self):
        conn = mock.Mock()
        api = self._get_api_with_mocked_conn(conn)
        public_key = "ssh-file deadbeef dave@isis"
        public_key_io = StringIO(public_key)

        rebuild_node = Node('1', 'server1', None, ['50.50.50.50'], [], None)
        conn.list_nodes.return_value = [rebuild_node]

        with mock.patch('littlechef_rackspace.api.time'):
            api.rebuild_node(name='server1',
                             image="image-id",
                             public_key_file=public_key_io)

        call_kwargs = conn.ex_rebuild.call_args_list[0][1]

        self.assertEqual(call_kwargs["node"].id, rebuild_node.id)
        self.assertEqual(call_kwargs["image"].id, "image-id")
        self.assertEquals(call_kwargs['ex_files'],
                          {"/root/.ssh/authorized_keys": public_key})

    def test_rebuild_node_with_progress(self):
        conn = mock.Mock()
        conn.ex_rebuild.return_value = True
        api = self._get_api_with_mocked_conn(conn)
        progress = StringIO()

        rebuild_node = Node('1', 'server1', None, ['50.50.50.50'], [], None)
        conn.list_nodes.return_value = [rebuild_node]

        with mock.patch('littlechef_rackspace.api.time'):
            api.rebuild_node(name='server1',
                             image="image-id",
                             public_key_file=StringIO("some key"),
                             progress=progress)

            self.assertEquals([
                "Rebuilding node {0} ({1})...".format(rebuild_node.name,
                                                      rebuild_node.id),
                'Waiting for node to begin rebuilding{0}'.format("."),
                "Waiting for node to become active{0}".format("." * 5),
                "Node active! (host: 50.2.3.4)"
            ], progress.getvalue().splitlines())

    def _get_api(self, region):
        return RackspaceApi(self.username, self.key, region)
