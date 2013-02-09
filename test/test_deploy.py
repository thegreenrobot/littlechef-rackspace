import unittest
import littlechef
import mock
from littlechef_rackspace.lib import Host
from littlechef_rackspace.deploy import ChefDeployer
from littlechef import runner as lc

class ChefDeployerTest(unittest.TestCase):

    def setUp(self):
        self.host = Host(host_string="50.56.57.58")

        self.deploy_chef = mock.Mock(spec=lc.deploy_chef)
        self.node = mock.Mock(spec=lc.node)

        self.chef = mock.Mock(spec=littlechef.chef)
        self.lib = mock.Mock(spec=littlechef.lib)
        self.lib.get_node.return_value = {}
        self.ohai_cloud = {}

    def _get_deployer(self, key_filename):
        deployer = ChefDeployer(key_filename=key_filename)
        deployer._get_cloud_ohai_attrs = mock.Mock(return_value=self.ohai_cloud)

        return deployer

    def test_deploy_sets_fabric_env(self):
        deployer = self._get_deployer(key_filename="~/.ssh/id_rsa")
        with mock.patch.multiple('littlechef_rackspace.deploy.lc',
                                 deploy_chef=self.deploy_chef, node=self.node),\
             mock.patch.multiple('littlechef_rackspace.deploy.littlechef',
                                 chef=self.chef, lib=self.lib):
            deployer.deploy(self.host)

        self.assertEquals(self.host.host_string, lc.env.host)
        self.assertEquals(self.host.host_string, lc.env.host_string)

    def test_deploy_sets_fabric_user_and_key_filename(self):
        key_filename = "~/.ssh/bootstrap_rsa"
        deployer = self._get_deployer(key_filename=key_filename)
        with mock.patch.multiple('littlechef_rackspace.deploy.lc',
                                 deploy_chef=self.deploy_chef, node=self.node),\
             mock.patch.multiple('littlechef_rackspace.deploy.littlechef',
                                 chef=self.chef, lib=self.lib):
            deployer.deploy(self.host)

        self.assertEquals("root", lc.env.user)
        self.assertEquals(key_filename, lc.env.key_filename)

    def test_deploy_calls_deploys_chef(self):
        deployer = self._get_deployer(key_filename="~/.ssh/id_rsa")

        with mock.patch.multiple('littlechef_rackspace.deploy.lc',
                                 deploy_chef=self.deploy_chef, node=self.node),\
             mock.patch.multiple('littlechef_rackspace.deploy.littlechef',
                                 chef=self.chef, lib=self.lib):
            deployer.deploy(self.host)
            self.deploy_chef.assert_any_call(ask="no")

    def test_deploy_with_no_runlist_calls_save_config(self):
        deployer = self._get_deployer(key_filename="~/.ssh/id_rsa")

        with mock.patch.multiple('littlechef_rackspace.deploy.lc',
                                deploy_chef=self.deploy_chef, node=self.node),\
             mock.patch.multiple('littlechef_rackspace.deploy.littlechef',
                                 chef=self.chef, lib=self.lib):
            deployer.deploy(self.host)
            self.chef.save_config.assert_any_call({'cloud': self.ohai_cloud})

    def test_deploy_with_runlist_sets_node_runlist(self):
        deployer = self._get_deployer(key_filename="~/.ssh/id_rsa")

        with mock.patch('littlechef_rackspace.deploy.lc'),\
             mock.patch.multiple('littlechef_rackspace.deploy.littlechef',
                                 chef=self.chef, lib=self.lib):
            self.lib.get_node.return_value = {'run_list': []}

            runlist = ['role[web]', 'recipe[apache2]']
            deployer.deploy(self.host, runlist=runlist)

            self.chef.sync_node.assert_any_call({ 'run_list': runlist,
                                                  'cloud': self.ohai_cloud})
            self.lib.get_node.assert_any_call(self.host.host_string)
