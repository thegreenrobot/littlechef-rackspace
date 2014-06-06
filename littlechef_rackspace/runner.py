from optparse import OptionParser
from fabric.utils import abort

import ConfigParser
import os
import littlechef
import yaml

from api import RackspaceApi
from deploy import ChefDeployer
from commands import (RackspaceCreate,
                      RackspaceListImages,
                      RackspaceListFlavors,
                      RackspaceListNetworks,
                      RackspaceRebuild,
                      RackspaceListServers)


def get_command_classes():
    return [RackspaceCreate,
            RackspaceRebuild,
            RackspaceListImages,
            RackspaceListFlavors,
            RackspaceListNetworks,
            RackspaceListServers]


class FailureMessages:

    INVALID_REGION = ("Must specify a valid region "
                      "'dfw', 'ord', 'iad', 'syd', 'hkg', 'lon'.")

    NEED_API_KEY = ("Must specify username, API key, and region "
                    "on command line or in [rackspace] configuration "
                    "section of config.cfg")

    MISSING_REQUIRED_ARGUMENTS = "Missing required arguments"

    MUST_SPECIFY_PUBLICNET = ("Must specify PublicNet in networks "
                              "list (id=00000000-0000-0000-0000-000000000000)")


class RackspaceOptionParser(OptionParser):
    def print_help(self, file=None):
        OptionParser.print_help(self, file)
        print("\nAvailable commands:\n")
        for command_class in get_command_classes():
            print("   {0}\t{1}".format(command_class.name,
                                       command_class.description))
        print("")


parser = RackspaceOptionParser()
parser.add_option("-I", "--image", dest="image",
                  help="Image ID")
parser.add_option("-f", "--flavor", dest="flavor",
                  help="Flavor ID")
parser.add_option("-A", "--username", dest="username",
                  help="Rackspace Username")
parser.add_option("-N", "--name", dest="name",
                  help="Node name (will become hostname for node)")
parser.add_option("-K", "--key", dest="key",
                  help="Rackspace API Key")
parser.add_option("-R", "--region", dest="region", default="",
                  help="Region for provisioning (required for OpenStack)")
parser.add_option("-a", "--public-key", dest="public_key",
                  help="Public Key File for Bootstrapping")
parser.add_option("-i", "--private-key", dest="private_key",
                  help="Private Key File for Bootstrapping")
parser.add_option("-r", "--runlist", dest="runlist",
                  help=("Node runlist delimited by commas, e.g. "
                        "'role[web],recipe[db]'"))
parser.add_option("-e", "--env", dest="environment",
                  help="Environment for newly created node",
                  default=None)
parser.add_option("-p", "--plugins", dest="plugins",
                  help=("Plugins to execute after chef bootstrapping but "
                        "before chef run e.g, 'save_cloud,save_hosts'"),
                  default=None)
parser.add_option("-P", "--post-plugins", dest="post-plugins",
                  help=("Plugins to execute after chef run. "
                        "e.g, 'mark_node_as_provisioned'"),
                  default=None)
parser.add_option("--skip-opscode-chef", action="store_false",
                  dest="use-opscode-chef")
parser.add_option("--dry-run", action="store_true", dest="dry_run",
                  help="When creating a node, do not actually create/deploy")
parser.add_option("--use-opscode-chef", type="int", dest="use-opscode-chef",
                  help=("Integer argument with whether or not to use "
                        "the OpsCode Chef repositorities "
                        "(installed with 'fix deploy_chef')"),
                  default=None)
parser.add_option("-n", "--networks", dest="networks",
                  help="Comma separated list of network ids to \
                          create node with (PublicNet is required)",
                  default=None)


class Runner(object):
    def _read_littlechef_config(self):
        try:
            config = ConfigParser.SafeConfigParser()
            success = config.read(littlechef.CONFIGFILE)
            if success:
                if os.path.isfile("rackspace.yaml"):
                    return yaml.load(file("rackspace.yaml"))
                elif os.path.isfile("rackspace.yml"):
                    return yaml.load(file("rackspace.yml"))
                else:
                    print(("WARNING: Reading configuration from deprecated "
                           "{0} file, consider upgrading to use "
                           "rackspace.yaml")
                          .format(littlechef.CONFIGFILE))
                    return dict(config.items('rackspace'))

            else:
                abort("Could not read littlechef configuration file! "
                      "Make sure you are running in a "
                      "kitchen (fix new_kitchen).")
        except ConfigParser.ParsingError:
            pass
        except ConfigParser.NoSectionError:
            pass

        return None

    def __init__(self, options=None):
        self.command_classes = get_command_classes()
        if options is None:
            options = self._read_littlechef_config()

        self.options = options or {}

    def _read_secrets_file(self, secrets_file):
        if secrets_file:
            try:
                del self.options['secrets-file']
                secrets_file = os.path.expanduser(secrets_file)
                # yes, look at another config file
                secrets_config = ConfigParser.SafeConfigParser()
                secrets_config.read(secrets_file)
                # assert _
                return dict(secrets_config.items(ConfigParser.DEFAULTSECT))
            except ConfigParser.ParsingError:
                pass

        return {}

    def get_api(self):
        username = self.options.get('username')
        key = self.options.get('key')
        region = self.options.get('region', '').lower()

        if region not in ['dfw', 'ord', 'syd', 'lon', 'iad', 'hkg']:
            abort(FailureMessages.INVALID_REGION)

        return RackspaceApi(username=username, key=key, region=region)

    def get_deploy(self):
        key_filename = self.options.get("private_key", "~/.ssh/id_rsa")
        return ChefDeployer(key_filename=key_filename)

    def _expand_argument(self, args, key):
        if args.get(key) and not isinstance(args.get(key), list):
            args[key.replace('-', '_')] = args[key].split(',')

    def main(self, cmd_args):
        (options, args) = parser.parse_args(cmd_args)

        if not args:
            raise InvalidCommand

        user_command = args[0]
        templates = args[1:]

        matched_commands = filter(lambda command_class:
                                  command_class.name == user_command,
                                  self.command_classes)

        if not matched_commands:
            raise InvalidCommand

        for k, v in vars(options).items():
            if v is not None and v != '':
                self.options[k] = v

        config_templates = self.options.get('templates', {})
        if 'templates' in self.options:
            del self.options['templates']

        for template in templates:
            if template not in config_templates:
                raise InvalidTemplate

            template_arguments = config_templates.get(template)
            for key, value in template_arguments.iteritems():
                if key not in self.options:
                    self.options[key] = value
                elif isinstance(self.options[key], list):
                    self.options[key] += value
                else:
                    self.options[key] = value

        self.options.update(self._read_secrets_file(
                            self.options.get('secrets-file')))

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

        self._expand_argument(args, 'runlist')
        self._expand_argument(args, 'plugins')
        self._expand_argument(args, 'post-plugins')
        self._expand_argument(args, 'networks')

        if 'use-opscode-chef' in args:
            args['use_opscode_chef'] = bool(args['use-opscode-chef'])

        if user_command == 'create' and 'networks' in args:
            if '00000000-0000-0000-0000-000000000000' not in args['networks']:
                raise InvalidConfiguration(
                    FailureMessages.MUST_SPECIFY_PUBLICNET
                )

        command.execute(**args)


class MissingRequiredArguments(Exception):
    pass


class InvalidConfiguration(Exception):
    pass


class InvalidCommand(Exception):
    pass


class InvalidTemplate(Exception):
    pass
