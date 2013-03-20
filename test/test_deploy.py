from StringIO import StringIO
import unittest
import mock
from littlechef_rackspace.lib import Host
from littlechef_rackspace.deploy import ChefDeployer

class ChefDeployerTest(unittest.TestCase):

    def setUp(self):
        self.host = Host(host_string="test.example.com",
                         ip_address="50.56.57.58")
        self.ohai_data = {
            'cloud': {
                'inet1_address': '1.2.3.4'
            },
            'network': {
                'eth0': 'eth 0 data',
                'eth1': 'eth 1 data'
            },
            'hostname': 'test',
            'keys': {
                'ssh': {
                    'public_keys': 'yep'
                }
            }
        }

    def _get_deployer(self, key_filename):
        deployer = ChefDeployer(key_filename=key_filename,)
        deployer._get_ohai_attrs_from_node = mock.Mock(return_value=self.ohai_data)
        deployer._create_bootstrap_ssh_config = mock.Mock()

        return deployer

    @mock.patch('littlechef_rackspace.deploy.lc')
    @mock.patch('littlechef_rackspace.deploy.littlechef')
    def test_deploy_sets_fabric_user_and_key_filename(self, littlechef, lc):
        key_filename = "~/.ssh/bootstrap_rsa"
        deployer = self._get_deployer(key_filename=key_filename)
        deployer.deploy(self.host)

        self.assertEquals("root", lc.env.user)
        self.assertEquals(key_filename, lc.env.key_filename)

    @mock.patch('littlechef_rackspace.deploy.lc')
    @mock.patch('littlechef_rackspace.deploy.littlechef')
    def test_deploy_calls_deploys_chef(self, littlechef, lc):
        deployer = self._get_deployer(key_filename="~/.ssh/id_rsa")

        deployer.deploy(self.host)

        lc.deploy_chef.assert_any_call(ask="no")

    @mock.patch('littlechef_rackspace.deploy.lc')
    @mock.patch('littlechef_rackspace.deploy.littlechef')
    def test_deploy_with_no_runlist_calls_save_config(self, littlechef, lc):
        deployer = self._get_deployer(key_filename="~/.ssh/id_rsa")

        node_data = {
            'predefined': 'data'
        }
        littlechef.lib.get_node.return_value = node_data

        deployer.deploy(self.host)

        littlechef.lib.get_node.assert_any_call(self.host.host_string)
        node_data.update(self.ohai_data)
        littlechef.chef.save_config.assert_any_call(node_data, force=True)

    @mock.patch('littlechef_rackspace.deploy.lc')
    @mock.patch('littlechef_rackspace.deploy.littlechef')
    def test_deploy_without_hostname_gets_node_with_ip_address(self, littlechef, lc):
        deployer = self._get_deployer(key_filename="~/.ssh/id_rsa")

        node_data = {}
        self.host.host_string = None
        littlechef.lib.get_node.return_value = node_data

        deployer.deploy(self.host)

        littlechef.lib.get_node.assert_any_call(self.host.ip_address)

    @mock.patch('littlechef_rackspace.deploy.lc')
    @mock.patch('littlechef_rackspace.deploy.littlechef')
    def test_deploy_with_runlist_sets_node_runlist(self, littlechef, lc):
        deployer = self._get_deployer(key_filename="~/.ssh/id_rsa")

        predefined_data = {'run_list': []}
        littlechef.lib.get_node.return_value = predefined_data

        runlist = ['role[web]', 'recipe[apache2]']
        deployer.deploy(self.host, runlist=runlist)

        predefined_data.update(self.ohai_data)
        predefined_data['run_list'] = runlist

        littlechef.chef.save_config.assert_any_call(predefined_data, force=True)
        littlechef.lib.get_node.assert_any_call(self.host.host_string)

    @mock.patch('littlechef_rackspace.deploy.lc')
    @mock.patch('littlechef_rackspace.deploy.littlechef')
    def test_deploy_with_environment_sets_environment(self, littlechef, lc):
        deployer = self._get_deployer(key_filename="~/.ssh/id_rsa")
        self.host.environment = 'staging'

        expected_data = { 'chef_environment' : 'staging' }
        expected_data.update(self.ohai_data)
        littlechef.lib.get_node.return_value = expected_data

        deployer.deploy(self.host)

        littlechef.chef.save_config.assert_any_call(expected_data, force=True)

    @mock.patch('littlechef_rackspace.deploy.lc')
    @mock.patch('littlechef_rackspace.deploy.littlechef')
    def test_deploy_with_runlist_creates_temporary_ssh_config_file(self, littlechef, lc):
        deployer = self._get_deployer(key_filename="~/.ssh/id_rsa")

        deployer.deploy(self.host)

        expected_ssh_config = """User root
IdentityFile ~/.ssh/id_rsa
StrictHostKeyChecking no
Host test.example.com
HostName 50.56.57.58
"""

        deployer._create_bootstrap_ssh_config.assert_any_call("./.bootstrap-config", expected_ssh_config)

    @mock.patch('littlechef_rackspace.deploy.lc')
    @mock.patch('littlechef_rackspace.deploy.littlechef')
    def test_deploy_with_runlist_uses_temporary_ssh_config_values(self, littlechef, lc):
        deployer = self._get_deployer(key_filename="~/.ssh/id_rsa")

        deployer.deploy(self.host)

        self.assertTrue(lc.env.use_ssh_config)
        self.assertEquals(lc.env.ssh_config_path, "./.bootstrap-config")

    @mock.patch('littlechef_rackspace.deploy.lc')
    @mock.patch('littlechef_rackspace.deploy.littlechef')
    def test_deploy_with_runlist_runs_node_on_ip_address(self, littlechef, lc):
        deployer = self._get_deployer(key_filename="~/.ssh/id_rsa")

        deployer.deploy(self.host)

        lc.node.assert_any_call(self.host.host_string)