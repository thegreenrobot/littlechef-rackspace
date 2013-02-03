from littlechef import runner as lc
import littlechef

class ChefDeployer(object):

    def __init__(self, key_filename):
        self.key_filename = key_filename

    def deploy(self, host, runlist=None):
        runlist = runlist or []

        lc.env.user = "root"
        lc.env.key_filename = self.key_filename
        lc.env.host = host.host_string
        lc.env.host_string = host.host_string
        lc.deploy_chef(ask="no")

        if runlist:
            data = littlechef.lib.get_node(host.host_string)
            data['run_list'] = runlist
            littlechef.chef.sync_node(data)
        else:
            lc.node(host.host_string)