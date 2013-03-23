import ConfigParser
import os
from optparse import OptionParser
from fabric.utils import abort
import littlechef
from api import RackspaceApi, Regions
from deploy import ChefDeployer
from commands import RackspaceCreate, RackspaceListImages, RackspaceListFlavors

def get_command_classes():
    return [RackspaceCreate,
            RackspaceListImages,
            RackspaceListFlavors]


class FailureMessages:

    NEED_API_KEY = ('Must specify username, API key, and region on command line '
                    'or in [rackspace] configuration section of config.cfg')

    MISSING_REQUIRED_ARGUMENTS = "Missing required arguments"


class RackspaceOptionParser(OptionParser):
    def print_help(self, file=None):
        OptionParser.print_help(self, file)
        print "\nAvailable commands:\n"
        for command_class in get_command_classes():
            print "   {0}\t{1}".format(command_class.name,
                                       command_class.description)
        print ""


parser = RackspaceOptionParser()
parser.add_option("-I", "--image", dest="image",
                  help="Image ID")
parser.add_option("-f", "--flavor", dest="flavor",
                  help="Flavor ID")
parser.add_option("-A", "--username", dest="username",
                  help="Rackspace Username")
parser.add_option("-N", "--node-name", dest="node_name",
                  help="Node name")
parser.add_option("-K", "--key", dest="key",
                  help="Rackspace API Key")
parser.add_option("-R", "--region", dest="region", default="",
                  help="Region for provisioning (required for OpenStack)")
parser.add_option("-a", "--public-key", dest="public_key",
                  help="Public Key File for Bootstrapping")
parser.add_option("-i", "--private-key", dest="private_key",
                  help="Private Key File for Bootstrapping")
parser.add_option("-r", "--runlist", dest="runlist",
                  help="Node runlist delimited by commas, e.g. 'role[web],recipe[db]'")
parser.add_option("-e", "--env", dest="environment",
                  help="Environment for newly created node",
                  default=None)
parser.add_option("-H", "--hostname", dest="hostname",
                  help="Hostname for newly created node (DNS will not be set up -- you must do this manually)",
                  default=None)
parser.add_option("-p", "--plugins", dest="plugins",
                  help="Plugins to execute after chef bootstrapping but before chef run e.g, 'save_cloud,save_hosts'",
                  default=None)
parser.add_option("-P", "--post-plugins", dest="post-plugins",
                  help="Plugins to execute after chef run. e.g, 'mark_node_as_provisioned'",
                  default=None)

class Runner(object):
    def _read_littlechef_config(self):
        try:
            config = ConfigParser.SafeConfigParser()
            success = config.read(littlechef.CONFIGFILE)
            if success:
                return dict(config.items('rackspace'))
            else:
                abort("Could not read littlechef configuration file!  "
                      "Make sure you are running in a kitchen (fix new_kitchen).")
        except ConfigParser.ParsingError:
            pass
        except ConfigParser.NoSectionError as e:
            pass

        return None

    def __init__(self, options=None):
        self.command_classes = get_command_classes()
        if options is None:
            options = self._read_littlechef_config()

        self.options = options or {}

        secrets_file = self.options.get('secrets-file')
        if secrets_file:
            try:
                del self.options['secrets-file']
                secrets_file = os.path.expanduser(secrets_file)
                # yes, look at another config file
                secrets_config = ConfigParser.SafeConfigParser()
                _ = secrets_config.read(secrets_file)
                self.options.update(dict(secrets_config.items(ConfigParser.DEFAULTSECT)))
            except ConfigParser.ParsingError:
                pass

    def get_api(self):
        username = self.options.get('username')
        key = self.options.get('key')
        region = self.options.get('region', '')
        if region.lower() == 'dfw':
            region = Regions.DFW
        elif region.lower() == 'ord':
            region = Regions.ORD
        else:
            region = Regions.NOT_FOUND

        if not username or not key or not region:
            abort(FailureMessages.NEED_API_KEY)

        return RackspaceApi(username=username, key=key, region=region)

    def get_deploy(self):
        key_filename = self.options.get("private_key", "~/.ssh/id_rsa")
        return ChefDeployer(key_filename=key_filename)

    def main(self, cmd_args):
        (options, args) = parser.parse_args(cmd_args)

        if not args:
            raise InvalidCommand

        user_command = args[0]
        matched_commands = filter(lambda command_class: command_class.name == user_command,
                                  self.command_classes)

        if not matched_commands:
            raise InvalidCommand

        for k, v in vars(options).items():
            if v:
                self.options[k] = v

        command_class = matched_commands[0]
        command_kwargs = {'rackspace_api': None,
                          'chef_deployer': None}

        if command_class.requires_api:
            command_kwargs['rackspace_api'] = self.get_api()
        if command_class.requires_deploy:
            command_kwargs['chef_deployer'] = self.get_deploy()

        command = command_class(**command_kwargs)

        args = self.options

        if not command.validate_args(**args):
            abort(FailureMessages.MISSING_REQUIRED_ARGUMENTS)
            return

        public_key = args.get('public_key', "~/.ssh/id_rsa.pub")
        args['public_key_file'] = file(os.path.expanduser(public_key))

        if args.get('runlist'):
            args['runlist'] = args['runlist'].split(',')

        if args.get('plugins'):
            args['plugins'] = args['plugins'].split(',')

        if args.get('post-plugins'):
            args['post_plugins'] = args['post-plugins'].split(',')

        command.execute(**args)

class MissingRequiredArguments(Exception):
    pass


class InvalidConfiguration(Exception):
    pass


class InvalidCommand(Exception):
    pass
