from fabric.operations import sudo, os
import simplejson as json
from fabric.context_managers import hide
from littlechef import runner as lc
import littlechef

class ChefDeployer(object):

    def __init__(self, key_filename):
        self.key_filename = key_filename

    def deploy(self, host, runlist=None):
        runlist = runlist or []
        ip_address = host.host_string

        self._deploy_chef(ip_address)
        self._save_node_data(ip_address, runlist)
        self._bootstrap_node(ip_address)

    def _deploy_chef(self, ip_address):
        lc.env.user = "root"
        lc.env.key_filename = self.key_filename
        lc.env.host = ip_address
        lc.env.host_string = ip_address
        lc.deploy_chef(ask="no")

    def _save_node_data(self, ip_address, runlist):
        """
        Save the runlist into the node data
        """

        data = littlechef.lib.get_node(ip_address)

        ohai = self._get_ohai_attrs()
        data['cloud'] = ohai['cloud']
        data['network'] = ohai['network']
        data['hostname'] = ohai['hostname']
        data['keys'] = ohai['keys']
        data['ipaddress'] = ip_address
        if runlist:
            data['run_list'] = runlist

        littlechef.chef.save_config(data, force=True)

    def _get_ohai_attrs(self):
        with hide('everything'):
            return json.loads(sudo("ohai"))

    def _bootstrap_node(self, ip_address):
        """
        New servers are created with 'root' user and an authorized public key
        that is a pair for the private key specified by self.key_filename.
        """

        # Set settings that don't have to do with our initial ssh config
        # (for example, encrypted data bag secret)
        littlechef.runner._readconfig()

        bootstrap_config_file = os.path.join(".", ".bootstrap-config")
        self._create_bootstrap_ssh_config(bootstrap_config_file)

        # Use the ssh config we've created
        lc.env.use_ssh_config = True
        lc.env.ssh_config_path = bootstrap_config_file
        lc.node(ip_address)

    def _create_bootstrap_ssh_config(self, bootstrap_config_file):
        """
        Create temporary config file used for node bootstrapping
        """

        bootstrap_ssh_config = open(bootstrap_config_file, mode="w")
        bootstrap_ssh_config.write("User root\nIdentityFile {key_filename}\nStrictHostKeyChecking no\n".format(
            key_filename=self.key_filename
        ))
        bootstrap_ssh_config.close()
        os.chmod(bootstrap_config_file, 0700)
        lc.env.ssh_config.parse(open(bootstrap_config_file))
