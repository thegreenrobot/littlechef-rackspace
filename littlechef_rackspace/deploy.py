import simplejson as json
from fabric.api import sudo
from fabric.context_managers import hide
from littlechef import runner as lc
import littlechef

class ChefDeployer(object):

    def __init__(self, key_filename):
        self.key_filename = key_filename

    def _get_cloud_ohai_attrs(self):
        with hide('everything'):
            ohai = json.loads(sudo("ohai"))
        cloud = ohai['cloud']
        return cloud

    def deploy(self, host, runlist=None):
        runlist = runlist or []

        lc.env.user = "root"
        lc.env.key_filename = self.key_filename
        lc.env.host = host.host_string
        lc.env.host_string = host.host_string

        # Need to wipe these our or the following commands
        # sometimes fail -- not sure if there is a better
        # way to do this

        lc.env.encrypted_data_bag_secret = None
        lc.env.follow_symlinks = False
        lc.env.ssh_config_path = None

        lc.deploy_chef(ask="no")

        data = littlechef.lib.get_node(host.host_string)
        data['cloud'] = self._get_cloud_ohai_attrs()

        if runlist:
            data['run_list'] = runlist
            littlechef.chef.sync_node(data)

        littlechef.chef.save_config(data)

