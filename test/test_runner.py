from StringIO import StringIO
import unittest2 as unittest
import mock
from littlechef_rackspace.api import RackspaceApi
from littlechef_rackspace.commands import RackspaceCreate, RackspaceListImages
from littlechef_rackspace.deploy import ChefDeployer
from littlechef_rackspace.runner import Runner, InvalidConfiguration
from littlechef_rackspace.runner import InvalidCommand, FailureMessages
from littlechef_rackspace.runner import InvalidTemplate, parser


class AbortException(Exception):
    """
    Abort mock must terminate execution of script
    """
    pass


class RunnerTest(unittest.TestCase):

    def setUp(self):
        self.api_class = mock.Mock(spec=RackspaceApi)
        self.rackspace_api = self.api_class.return_value
        self.deploy_class = mock.Mock(spec=ChefDeployer)
        self.chef_deployer = self.deploy_class.return_value
        self.create_class = mock.Mock(spec=RackspaceCreate)
        self.abort = mock.Mock()
        self.abort.side_effect = AbortException

        self.create_class.name = 'create'

        self.create_command = self.create_class.return_value
        self.list_images_class = mock.Mock(spec=RackspaceListImages)
        self.list_images_class.name = 'list-images'

        self.list_images_command = self.list_images_class.return_value

        '''
        Dumb hacks using README.md as a public key because you can't
        mock out a file() call.
        '''

        self.create_base = "create --public-key README.md"
        self.create_args = ("{0} --flavor 2 --image 123 --name test-node " +
                            "--username username --key deadbeef " +
                            "--region dfw --public-key README.md"
                            ).format(self.create_base).split(' ')

        list_images_command_string = ("list-images --username username " +
                                      "--key deadbeef --region REGION " +
                                      "--public-key README.md"
                                      )

        self.dfw_list_images_args = list_images_command_string.replace(
            'REGION', 'dfw'
            ).split(' ')
        self.lon_list_images_args = list_images_command_string.replace(
            'REGION', 'lon'
            ).split(' ')
        self.syd_list_images_args = list_images_command_string.replace(
            'REGION', 'syd'
            ).split(' ')

    def test_must_specify_command(self):
        r = Runner(options={})
        with self.assertRaises(InvalidCommand):
            r.main([])

    def test_must_specify_existing_command(self):
        r = Runner(options={})
        with self.assertRaises(InvalidCommand):
            r.main(['bogus-command'])

    def test_parser_prints_help_formatted_to_longest_command_name(self):
        klass1 = mock.Mock()
        klass2 = mock.Mock()
        klass1.name = "short name"
        klass2.name = "X" * 100
        klasses = [klass1, klass2]

        class_to_patch = 'littlechef_rackspace.runner.get_command_classes'
        with mock.patch(class_to_patch) as get_command_classes:
            get_command_classes.return_value = klasses
            output = StringIO()
            parser.print_help(file=output)

            expected_output = ""
            for command_class in get_command_classes():
                name = command_class.name.ljust(100 + 3)
                description = command_class.description
                expected_output += "   {0}{1}\n".format(name, description)

            self.assertTrue(expected_output in output.getvalue())

    def test_list_images_fails_if_configuration_is_not_provided(self):
        with mock.patch.multiple(
                "littlechef_rackspace.runner",
                RackspaceApi=self.api_class,
                ChefDeployer=self.deploy_class,
                RackspaceListImages=self.list_images_class,
                abort=self.abort):
            with self.assertRaises(AbortException):
                r = Runner(options={})
                r.main(["list-images"])
                self.abort.assert_any_call(FailureMessages.NEED_API_KEY)

    def test_list_images_with_dfw_region_instantiates_api(self):
        with mock.patch.multiple(
                "littlechef_rackspace.runner",
                RackspaceApi=self.api_class,
                ChefDeployer=self.deploy_class,
                RackspaceListImages=self.list_images_class):
            r = Runner(options={})
            r.main(self.dfw_list_images_args)
            self.api_class.assert_any_call(username="username",
                                           key="deadbeef",
                                           region='dfw')

    def test_uses_config_settings(self):
        with mock.patch.multiple("littlechef_rackspace.runner",
                                 RackspaceApi=self.api_class,
                                 ChefDeployer=self.deploy_class,
                                 RackspaceListImages=self.list_images_class):
            r = Runner(options={
                'username': 'username',
                'key': 'deadbeef',
                'region': 'ord'
            })
            # another dumb hack
            r.main(['list-images', '--public-key', 'README.md'])
            self.api_class.assert_any_call(username="username",
                                           key="deadbeef",
                                           region='ord')

    def test_create_fails_if_configuration_is_not_provided(self):
        r = Runner(options={})
        with mock.patch.multiple('littlechef_rackspace.runner',
                                 abort=self.abort):
            with self.assertRaises(AbortException):
                r.main(["create"])
                self.abort.assert_any_call(FailureMessages.NEED_API_KEY)

    def test_create_fails_if_required_arguments_are_not_provided(self):
        with mock.patch.multiple('littlechef_rackspace.runner',
                                 abort=self.abort):
            with self.assertRaises(AbortException):
                self.create_command.validate_args.return_value = False
                r = Runner(options={})
                r.main(("create --username username --key deadbeef "
                       "--region dfw").split(" "))
                self.abort.assert_any_call(
                    FailureMessages.MISSING_REQUIRED_ARGUMENTS
                    )

    def test_create_instantiates_api_and_deploy_with_default_private_key(self):
        with mock.patch.multiple(
                "littlechef_rackspace.runner",
                RackspaceApi=self.api_class,
                ChefDeployer=self.deploy_class,
                RackspaceCreate=self.create_class):
            r = Runner(options={})
            r.main(self.create_args)

            self.api_class.assert_any_call(
                username="username",
                key="deadbeef",
                region='dfw')
            self.deploy_class.assert_any_call(key_filename="~/.ssh/id_rsa")

    def test_create_creates_node_with_specified_public_key(self):
        with mock.patch.multiple(
                "littlechef_rackspace.runner",
                RackspaceApi=self.api_class,
                ChefDeployer=self.deploy_class,
                RackspaceCreate=self.create_class):
            r = Runner(options={})
            r.main(self.create_args)

            self.create_class.assert_any_call(rackspace_api=self.rackspace_api,
                                              chef_deployer=self.chef_deployer)

            call_args = self.create_command.execute.call_args_list[0][1]

            self.assertEquals("123", call_args["image"])
            self.assertEquals("2", call_args["flavor"])
            self.assertEquals("test-node", call_args["name"])
            self.assertEquals('README.md', call_args['public_key_file'].name)

    def test_create_with_runlist_parses_runlist_into_array(self):
        with mock.patch.multiple(
                "littlechef_rackspace.runner",
                RackspaceApi=self.api_class,
                ChefDeployer=self.deploy_class,
                RackspaceCreate=self.create_class):
            r = Runner(options={})
            runlist = 'role[test],recipe[web],recipe[apache2]'
            r.main(self.create_args + ['--runlist', runlist])

            call_args = self.create_command.execute.call_args_list[0][1]
            self.assertEquals(runlist.split(','), call_args["runlist"])

    def test_create_with_plugins_parses_plugins_into_array(self):
        with mock.patch.multiple(
                "littlechef_rackspace.runner",
                RackspaceApi=self.api_class,
                ChefDeployer=self.deploy_class,
                RackspaceCreate=self.create_class):
            r = Runner(options={})
            plugins = 'plugin1,plugin2,plugin3'
            r.main(self.create_args + ['--plugins', plugins])

            call_args = self.create_command.execute.call_args_list[0][1]
            self.assertEquals(plugins.split(','), call_args["plugins"])

    def test_create_with_postplugins_parses_postplugins_into_array(self):
        with mock.patch.multiple(
                "littlechef_rackspace.runner",
                RackspaceApi=self.api_class,
                ChefDeployer=self.deploy_class,
                RackspaceCreate=self.create_class):
            r = Runner(options={})
            post_plugins = 'plugin1,plugin2,plugin3'
            r.main(self.create_args + ['--post-plugins', post_plugins])

            call_args = self.create_command.execute.call_args_list[0][1]
            self.assertEquals(
                post_plugins.split(','),
                call_args["post_plugins"]
                )

    def test_create_with_skip_opscode_chef_to_false(self):
        with mock.patch.multiple(
                "littlechef_rackspace.runner",
                RackspaceApi=self.api_class,
                ChefDeployer=self.deploy_class,
                RackspaceCreate=self.create_class):
            r = Runner(options={})
            r.main(self.create_args + ['--skip-opscode-chef'])

            call_args = self.create_command.execute.call_args_list[0][1]
            self.assertEquals(False, call_args["use_opscode_chef"])

    def test_create_without_skip_opscode_chef(self):
        with mock.patch.multiple(
                "littlechef_rackspace.runner",
                RackspaceApi=self.api_class,
                ChefDeployer=self.deploy_class,
                RackspaceCreate=self.create_class):
            r = Runner(options={})
            r.main(self.create_args)

            call_args = self.create_command.execute.call_args_list[0][1]
            self.assertEquals(None, call_args.get("use_opscode_chef"))

    def test_create_with_use_opscode_chef_to_false(self):
        with mock.patch.multiple(
                "littlechef_rackspace.runner",
                RackspaceApi=self.api_class,
                ChefDeployer=self.deploy_class,
                RackspaceCreate=self.create_class):
            r = Runner(options={})
            r.main(self.create_args + ['--use-opscode-chef', '0'])

            call_args = self.create_command.execute.call_args_list[0][1]
            self.assertEquals(False, call_args["use_opscode_chef"])

    def test_create_with_use_opscode_chef_to_true(self):
        with mock.patch.multiple(
                "littlechef_rackspace.runner",
                RackspaceApi=self.api_class,
                ChefDeployer=self.deploy_class,
                RackspaceCreate=self.create_class):
            r = Runner(options={})
            r.main(self.create_args + ['--use-opscode-chef', '1'])

            call_args = self.create_command.execute.call_args_list[0][1]
            self.assertEquals(True, call_args.get("use_opscode_chef"))

    def test_create_with_use_opscode_chef_not_specified(self):
        with mock.patch.multiple(
                "littlechef_rackspace.runner",
                RackspaceApi=self.api_class,
                ChefDeployer=self.deploy_class,
                RackspaceCreate=self.create_class):
            r = Runner(options={})
            r.main(self.create_args)

            call_args = self.create_command.execute.call_args_list[0][1]
            self.assertFalse("use_opscode_chef" in call_args)

    def test_create_with_networks_without_publicnet_raises_exception(self):
        with mock.patch.multiple(
                "littlechef_rackspace.runner",
                RackspaceApi=self.api_class,
                ChefDeployer=self.deploy_class,
                RackspaceCreate=self.create_class):
            r = Runner(options={})
            with self.assertRaises(InvalidConfiguration) as cm:
                r.main(self.create_args + ['--networks', 'abcdefg'])

            self.assertEquals("Must specify PublicNet in networks list " +
                              "(id=00000000-0000-0000-0000-000000000000)",
                              cm.exception.message)

    def test_list_images_without_publicnet_does_not_raise_exception(self):
        with mock.patch.multiple(
                "littlechef_rackspace.runner",
                RackspaceApi=self.api_class,
                ChefDeployer=self.deploy_class,
                RackspaceListImages=self.list_images_class):
            r = Runner(options={})
            r.main(self.dfw_list_images_args + ['--networks', 'abcdefg'])

            self.api_class.assert_any_call(username="username",
                                           key="deadbeef",
                                           region='dfw')

    def test_create_with_networks_passes_networks(self):
        with mock.patch.multiple(
                "littlechef_rackspace.runner",
                RackspaceApi=self.api_class,
                ChefDeployer=self.deploy_class,
                RackspaceCreate=self.create_class):
            r = Runner(options={})
            public_net_id = '00000000-0000-0000-0000-000000000000'
            custom_net_id = '45e8b288-3a98-4092-a3e8-37e2a540d004'
            r.main(self.create_args +
                   ['--networks', '{0},{1}'.format(
                    public_net_id,
                    custom_net_id)]
                   )

            call_args = self.create_command.execute.call_args_list[0][1]
            self.assertEquals([public_net_id, custom_net_id],
                              call_args.get('networks'))

    def test_create_with_template_includes_template(self):
        with mock.patch.multiple(
                "littlechef_rackspace.runner",
                RackspaceApi=self.api_class,
                ChefDeployer=self.deploy_class,
                RackspaceCreate=self.create_class):
            r = Runner(options={
                'templates': {
                    'preprod': {
                        'region': 'dfw'
                    },
                    'web': {
                        'image': 'Ubuntu 12.04-Image',
                        'flavor': 'performance1-2',
                        'runlist': [
                            'role[web]'
                        ],
                        'networks': [
                            '00000000-0000-0000-0000-000000000000'
                        ]
                    }
                }
            })

            r.main('{0} --name test preprod web'.format(
                self.create_base).split(' '))

            call_args = self.create_command.execute.call_args_list[0][1]
            self.assertEquals('performance1-2', call_args.get('flavor'))
            self.assertEquals('Ubuntu 12.04-Image', call_args.get('image'))
            self.assertEquals(['role[web]'], call_args.get('runlist'))
            self.assertEquals('dfw', call_args.get('region'))

    def test_create_with_template_that_has_secrets_file_includes_values(self):
        with mock.patch.multiple(
                "littlechef_rackspace.runner",
                RackspaceApi=self.api_class,
                ChefDeployer=self.deploy_class,
                RackspaceCreate=self.create_class):
            r = Runner(options={
                'templates': {
                    'preprod': {
                        'secrets-file': 'secrets-test.cfg',
                        'region': 'dfw'
                    }
                }
            })
            r._read_secrets_file = mock.Mock(return_value={
                'username': 'testuser',
                'key': 'testuserkey'
            })

            r.main('{0} --name test preprod'.format(
                self.create_base).split(' '))

            call_args = self.create_command.execute.call_args_list[0][1]
            r._read_secrets_file.assert_any_call('secrets-test.cfg')
            self.assertEquals('testuser', call_args.get('username'))
            self.assertEquals('testuserkey', call_args.get('key'))

    def test_create_with_template_does_not_pass_templates_to_create_cmd(self):
        with mock.patch.multiple(
                "littlechef_rackspace.runner",
                RackspaceApi=self.api_class,
                ChefDeployer=self.deploy_class,
                RackspaceCreate=self.create_class):
            r = Runner(options={
                'templates': {
                    'web': {
                        'image': 'Ubuntu 13.10'
                        }
                    }})
            r.main(self.create_args)

            call_args = self.create_command.execute.call_args_list[0][1]
            self.assertTrue('templates' not in call_args)

    def test_create_with_multiple_template_merges_array_arguments(self):
        with mock.patch.multiple(
                "littlechef_rackspace.runner",
                RackspaceApi=self.api_class,
                ChefDeployer=self.deploy_class,
                RackspaceCreate=self.create_class):
            templates = {
                'templates': {
                    'test1': {
                        'region': 'dfw',
                        'runlist': ['role[test1]']
                    },
                    'test2': {
                        'runlist': ['role[test2]']
                    }
                }
            }
            r = Runner(options=templates)
            r.main('{0} test1 test2 --name test'.format(
                self.create_base).split())

            call_args = self.create_command.execute.call_args_list[0][1]
            self.assertEquals(['role[test1]', 'role[test2]'],
                              call_args['runlist'])

    def test_create_with_invalid_templates_raises_error(self):
        with mock.patch.multiple(
                "littlechef_rackspace.runner",
                RackspaceApi=self.api_class,
                ChefDeployer=self.deploy_class,
                RackspaceCreate=self.create_class):
            r = Runner(options={})
            with self.assertRaises(InvalidTemplate):
                r.main('{0} --name test invalidtemplate'.format(
                    self.create_base).split(' '))
