import ConfigParser
import os
import sys
from optparse import OptionParser
import littlechef
from api import RackspaceApi, Regions
from deploy import ChefDeployer
from commands import RackspaceCreate, RackspaceListImages, RackspaceListFlavors

def get_command_classes():
    return [RackspaceCreate,
            RackspaceListImages,
            RackspaceListFlavors]


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

class Runner(object):
    def _read_littlechef_config(self):
        try:
            config = ConfigParser.SafeConfigParser()
            success = config.read(littlechef.CONFIGFILE)
            if success:
                return dict(config.items('rackspace'))
        except ConfigParser.ParsingError:
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

    def get_api(self, options):
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
            raise InvalidConfiguration('Must specify username, API key, and region')

        return RackspaceApi(username=username, key=key, region=region)

    def get_deploy(self, options):
        key_filename = options.private_key or "~/.ssh/id_rsa"
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
            command_kwargs['rackspace_api'] = self.get_api(options)
        if command_class.requires_deploy:
            command_kwargs['chef_deployer'] = self.get_deploy(options)

        command = command_class(**command_kwargs)
        args = vars(options)

        if not command.validate_args(**args):
            raise MissingRequiredArguments("Missing required arguments")

        public_key = args['public_key'] or "~/.ssh/id_rsa.pub"
        args['public_key_file'] = file(os.path.expanduser(public_key))

        if args['runlist']:
            args['runlist'] = args['runlist'].split(',')

        args['progress'] = sys.stdout

        command.execute(**args)

class MissingRequiredArguments(Exception):
    pass


class InvalidConfiguration(Exception):
    pass


class InvalidCommand(Exception):
    pass
