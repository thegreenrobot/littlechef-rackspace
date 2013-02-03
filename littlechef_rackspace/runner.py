import sys
from optparse import OptionParser
from api import RackspaceApi, Regions
from deploy import ChefDeployer
from commands import RackspaceCreate, RackspaceListImages

def get_command_classes():
    return [RackspaceCreate, RackspaceListImages]


class RackspaceOptionParser(OptionParser):
    def print_help(self, file=None):
        OptionParser.print_help(self, file)
        print "\nAvailable commands:\n"
        for command_class in get_command_classes():
            print "   {0}\t{1}".format(command_class.name,
                                       command_class.description)
        print ""


parser = RackspaceOptionParser()
parser.add_option("-I", "--image", dest="image_id",
                  help="Image ID")
parser.add_option("-f", "--flavor", dest="flavor_id",
                  help="Flavor ID")
parser.add_option("-A", "--username", dest="username",
                  help="Rackspace Username")
parser.add_option("-N", "--node-name", dest="node_name",
                  help="Node name")
parser.add_option("-K", "--key", dest="apikey",
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
    def __init__(self):
        self.command_classes = get_command_classes()

    def _get_command(self):
        pass

    def get_api(self, options):
        if not options.username or not options.apikey or not options.region:
            raise InvalidConfiguration('Must specify username, API key, and region')

        username = options.username
        apikey = options.apikey
        if options.region.lower() == 'dfw':
            region = Regions.DFW
        else:
            region = Regions.ORD

        return RackspaceApi(username=username, apikey=apikey, region=region)

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

        command_class = matched_commands[0]

        command_kwargs = {'rackspace_api': None,
                          'chef_deployer': None}

        if command_class.requires_api:
            command_kwargs['rackspace_api'] = self.get_api(options)
        if command_class.requires_deploy:
            command_kwargs['chef_deployer'] = self.get_deploy(options)

        command = command_class(**command_kwargs)

        args = vars(options)
        if args['public_key']:
            args['public_key_file'] = file(args['public_key'])
        else:
            args['public_key_file'] = file('~/.ssh/id_rsa.pub')

        if args['runlist']:
            args['runlist'] = args['runlist'].split(',')

        try:
            command.execute(**args)
        except TypeError:
            raise MissingRequiredArguments("Missing required arguments")


class MissingRequiredArguments(Exception):
    pass


class InvalidConfiguration(Exception):
    pass


class InvalidCommand(Exception):
    pass

if __name__ == "__main__":
    r = Runner()
    try:
        r.main(sys.argv[1:])
    except MissingRequiredArguments:
        print "Not all arguments for command provided"
        parser.print_help()
    except InvalidConfiguration:
        print "Could not determine API configuration: must specify username, api key, and region"
        parser.print_help()
    except InvalidCommand:
        print "Invalid command specified"
        parser.print_help()