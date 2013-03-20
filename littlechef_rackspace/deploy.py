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

        self._deploy_chef(host)
        self._save_node_data(host, runlist)
        self._bootstrap_node(host)

    def _deploy_chef(self, host):
        lc.env.user = "root"
        lc.env.key_filename = self.key_filename
        lc.env.host = host.ip_address
        lc.env.host_string = host.ip_address
        lc.deploy_chef(ask="no")

    def _save_node_data(self, host, runlist):
        """
        Save the runlist into the node data
        """

        ohai = self._get_ohai_attrs_from_node(host)

        data = littlechef.lib.get_node(host.get_host_string())
        data['cloud'] = ohai['cloud']
        data['network'] = ohai['network']
        data['hostname'] = ohai['hostname']
        data['keys'] = ohai['keys']
        data['ipaddress'] = host.ip_address
        if host.environment:
            data['chef_environment'] = host.environment
        if runlist:
            data['run_list'] = runlist

        littlechef.chef.save_config(data, force=True)

    def _get_ohai_attrs_from_node(self, host):
        lc.env.host_string = host.ip_address
        with hide('everything'):
            ohai = json.loads(sudo("ohai"))

        lc.env.host_string = host.get_host_string()
        return ohai

    def _bootstrap_node(self, host):
        """
        New servers are created with 'root' user and an authorized public key
        that is a pair for the private key specified by self.key_filename.
        """

        # Set settings that don't have to do with our initial ssh config
        # (for example, encrypted data bag secret)
        littlechef.runner._readconfig()

        bootstrap_config_file = os.path.join(".", ".bootstrap-config")
        contents = ("User root\n"
                    "IdentityFile {key_filename}\n"
                    "StrictHostKeyChecking no\n"
                    "Host {host_string}\n"
                    "HostName {ip_address}\n").format(key_filename=self.key_filename,
                                                      host_string=host.get_host_string(),
                                                      ip_address=host.ip_address)

        self._create_bootstrap_ssh_config(bootstrap_config_file, contents)

        # Use the ssh config we've created
        lc.env.use_ssh_config = True
        lc.env.ssh_config_path = bootstrap_config_file
        lc.node(host.get_host_string())

    def _create_bootstrap_ssh_config(self, bootstrap_config_file, contents):
        """
        Create temporary config file used for node bootstrapping
        """

        bootstrap_ssh_config = open(bootstrap_config_file, mode="w")
        bootstrap_ssh_config.write(contents)
        bootstrap_ssh_config.close()
        os.chmod(bootstrap_config_file, 0700)
        lc.env.ssh_config.parse(open(bootstrap_config_file))
