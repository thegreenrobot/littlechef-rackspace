from fabric.operations import sudo, os
import simplejson as json
from fabric.context_managers import hide
from littlechef import runner as lc
import littlechef

class ChefDeployer(object):

    def __init__(self, key_filename):
        self.key_filename = key_filename

    def deploy(self, host, runlist=None, plugins=None, post_plugins=None,
               use_opscode_chef=True, **kwargs):
        runlist = runlist or []
        plugins = plugins or []
        post_plugins = post_plugins or []

        self._setup_ssh_config(host)
        if use_opscode_chef:
            lc.deploy_chef(ask="no")

        self._save_node_data(host, runlist)
        for plugin in plugins:
            self._execute_plugin(host, plugin)

        self._bootstrap_node(host)

        for plugin in post_plugins:
            self._execute_plugin(host, plugin)

    def _save_node_data(self, host, runlist):
        """
        Save the runlist and environment into the node data
        """

        data = littlechef.lib.get_node(host.get_host_string())
        if host.environment:
            data['chef_environment'] = host.environment
        if runlist:
            data['run_list'] = runlist

        littlechef.chef.save_config(data, force=True)

    def _execute_plugin(self, host, plugin_name):
        node = littlechef.lib.get_node(host.get_host_string())
        plugin = littlechef.lib.import_plugin(plugin_name)
        littlechef.lib.print_header("Executing plugin '{0}' on "
                                    "{1}".format(plugin_name, lc.env.host_string))

        plugin.execute(node)

    def _setup_ssh_config(self, host):
        """
        New servers are created with 'root' user and an authorized public key
        that is a pair for the private key specified by self.key_filename.
        """

        # Set settings that don't have to do with our initial ssh config
        # (for example, encrypted data bag secret)
        littlechef.runner._readconfig()

        bootstrap_config_file = os.path.join(".", ".bootstrap-config_{0}".format(host.get_host_string()))
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

        # Setup ssh config
        lc.env.user = "root"
        lc.env.host = host.get_host_string()
        lc.env.host_string = host.get_host_string()

    def _bootstrap_node(self, host):
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
