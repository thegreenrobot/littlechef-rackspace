import unittest2 as unittest
import mock
from littlechef_rackspace.api import Regions, RackspaceApi
from littlechef_rackspace.commands import RackspaceCreate, RackspaceListImages
from littlechef_rackspace.deploy import ChefDeployer
from littlechef_rackspace.runner import Runner, MissingRequiredArguments, InvalidConfiguration, InvalidCommand, FailureMessages


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
        self.abort=mock.Mock()
        self.abort.side_effect = AbortException

        self.create_class.name = 'create'

        self.create_command = self.create_class.return_value
        self.list_images_class = mock.Mock(spec=RackspaceListImages)
        self.list_images_class.name = 'list-images'

        self.list_images_command = self.list_images_class.return_value

        # Dumb hacks using README.md as a public key because you can't mock out a file() call
        self.create_args = "create --flavor 2 --image 123 --node-name test-node --username username --key deadbeef --region dfw --public-key README.md".split(' ')

        list_images_command_string = "list-images --username username --key deadbeef --region REGION --public-key README.md"
        self.dfw_list_images_args = list_images_command_string.replace('REGION', 'dfw').split(' ')
        self.lon_list_images_args = list_images_command_string.replace('REGION', 'lon').split(' ')
        self.syd_list_images_args = list_images_command_string.replace('REGION', 'syd').split(' ')

    def test_must_specify_command(self):
        r = Runner(options={})
        with self.assertRaises(InvalidCommand):
            r.main([])

    def test_must_specify_existing_command(self):
        r = Runner(options={})
        with self.assertRaises(InvalidCommand):
            r.main(['bogus-command'])

    def test_list_images_fails_if_configuration_is_not_provided(self):
        with mock.patch.multiple("littlechef_rackspace.runner", RackspaceApi=self.api_class,
                                 ChefDeployer=self.deploy_class, RackspaceListImages=self.list_images_class,
                                 abort=self.abort):
            with self.assertRaises(AbortException):
                r = Runner(options={})
                r.main(["list-images"])
                self.abort.assert_any_call(FailureMessages.NEED_API_KEY)

    def test_list_images_with_dfw_region_instantiates_api(self):
        with mock.patch.multiple("littlechef_rackspace.runner", RackspaceApi=self.api_class,
                                 ChefDeployer=self.deploy_class, RackspaceListImages=self.list_images_class):
            r = Runner(options={})
            r.main(self.dfw_list_images_args)
            self.api_class.assert_any_call(username="username", key="deadbeef", region=Regions.DFW)

    def test_list_images_with_lon_region_instantiates_api(self):
        with mock.patch.multiple("littlechef_rackspace.runner", RackspaceApi=self.api_class,
                                 ChefDeployer=self.deploy_class, RackspaceListImages=self.list_images_class):
            r = Runner(options={})
            r.main(self.lon_list_images_args)
            self.api_class.assert_any_call(username="username", key="deadbeef", region=Regions.LON)

    def test_list_images_with_syd_region_instantiates_api(self):
        with mock.patch.multiple("littlechef_rackspace.runner", RackspaceApi=self.api_class,
                                 ChefDeployer=self.deploy_class, RackspaceListImages=self.list_images_class):
            r = Runner(options={})
            r.main(self.syd_list_images_args)
            self.api_class.assert_any_call(username="username", key="deadbeef", region=Regions.SYD)

    def test_uses_config_settings(self):
        with mock.patch.multiple("littlechef_rackspace.runner", RackspaceApi=self.api_class,
                                 ChefDeployer=self.deploy_class, RackspaceListImages=self.list_images_class):
            r = Runner(options={
                'username': 'username',
                'key': 'deadbeef',
                'region': 'ord'
            })
            # another dumb hack
            r.main(['list-images', '--public-key', 'README.md'])
            self.api_class.assert_any_call(username="username", key="deadbeef", region=Regions.ORD)

    def test_create_fails_if_configuration_is_not_provided(self):
        r = Runner(options={})
        with mock.patch.multiple('littlechef_rackspace.runner', abort=self.abort):
            with self.assertRaises(AbortException):
                r.main(["create"])
                self.abort.assert_any_call(FailureMessages.NEED_API_KEY)


    def test_create_fails_if_required_arguments_are_not_provided(self):
        with mock.patch.multiple('littlechef_rackspace.runner', abort=self.abort):
            with self.assertRaises(AbortException):
                self.create_command.validate_args.return_value = False
                r = Runner(options={})
                r.main("create --username username --key deadbeef --region dfw".split(" "))
                self.abort.assert_any_call(FailureMessages.MISSING_REQUIRED_ARGUMENTS)

    def test_create_instantiates_api_and_deploy_with_default_private_key(self):
        with mock.patch.multiple("littlechef_rackspace.runner", RackspaceApi=self.api_class,
                                 ChefDeployer=self.deploy_class, RackspaceCreate=self.create_class):
            r = Runner(options={})
            r.main(self.create_args)

            self.api_class.assert_any_call(username="username", key="deadbeef", region=Regions.DFW)
            self.deploy_class.assert_any_call(key_filename="~/.ssh/id_rsa")

    def test_create_creates_node_with_specified_public_key(self):
        with mock.patch.multiple("littlechef_rackspace.runner", RackspaceApi=self.api_class,
                                 ChefDeployer=self.deploy_class, RackspaceCreate=self.create_class):
            r = Runner(options={})
            r.main(self.create_args)

            self.create_class.assert_any_call(rackspace_api=self.rackspace_api,
                                              chef_deployer=self.chef_deployer)

            call_args = self.create_command.execute.call_args_list[0][1]

            self.assertEquals("123", call_args["image"])
            self.assertEquals("2", call_args["flavor"])
            self.assertEquals("test-node", call_args["node_name"])
            self.assertEquals('README.md', call_args['public_key_file'].name)

    def test_create_with_runlist_parses_runlist_into_array(self):
        with mock.patch.multiple("littlechef_rackspace.runner", RackspaceApi=self.api_class,
                                 ChefDeployer=self.deploy_class, RackspaceCreate=self.create_class):
            r = Runner(options={})
            runlist = 'role[test],recipe[web],recipe[apache2]'
            r.main(self.create_args + [ '--runlist', runlist ])

            call_args = self.create_command.execute.call_args_list[0][1]
            self.assertEquals(runlist.split(','), call_args["runlist"])

    def test_create_with_plugins_parses_plugins_into_array(self):
        with mock.patch.multiple("littlechef_rackspace.runner", RackspaceApi=self.api_class,
                                 ChefDeployer=self.deploy_class, RackspaceCreate=self.create_class):
            r = Runner(options={})
            plugins = 'plugin1,plugin2,plugin3'
            r.main(self.create_args + [ '--plugins', plugins ])

            call_args = self.create_command.execute.call_args_list[0][1]
            self.assertEquals(plugins.split(','), call_args["plugins"])

    def test_create_with_postplugins_parses_postplugins_into_array(self):
        with mock.patch.multiple("littlechef_rackspace.runner", RackspaceApi=self.api_class,
                                 ChefDeployer=self.deploy_class, RackspaceCreate=self.create_class):
            r = Runner(options={})
            post_plugins = 'plugin1,plugin2,plugin3'
            r.main(self.create_args + [ '--post-plugins', post_plugins ])

            call_args = self.create_command.execute.call_args_list[0][1]
            self.assertEquals(post_plugins.split(','), call_args["post_plugins"])

    def test_create_with_skip_opscode_chef_to_false(self):
        with mock.patch.multiple("littlechef_rackspace.runner", RackspaceApi=self.api_class,
                                 ChefDeployer=self.deploy_class, RackspaceCreate=self.create_class):
            r = Runner(options={})
            r.main(self.create_args + [ '--skip-opscode-chef'])

            call_args = self.create_command.execute.call_args_list[0][1]
            self.assertEquals(False, call_args["use_opscode_chef"])

    def test_create_without_skip_opscode_chef(self):
        with mock.patch.multiple("littlechef_rackspace.runner", RackspaceApi=self.api_class,
                                 ChefDeployer=self.deploy_class, RackspaceCreate=self.create_class):
            r = Runner(options={})
            r.main(self.create_args)

            call_args = self.create_command.execute.call_args_list[0][1]
            self.assertEquals(None, call_args.get("use_opscode_chef"))

    def test_create_with_use_opscode_chef_to_false(self):
        with mock.patch.multiple("littlechef_rackspace.runner", RackspaceApi=self.api_class,
                                 ChefDeployer=self.deploy_class, RackspaceCreate=self.create_class):
            r = Runner(options={})
            r.main(self.create_args + [ '--use-opscode-chef', '0'])

            call_args = self.create_command.execute.call_args_list[0][1]
            self.assertEquals(False, call_args["use_opscode_chef"])

    def test_create_with_use_opscode_chef_to_true(self):
        with mock.patch.multiple("littlechef_rackspace.runner", RackspaceApi=self.api_class,
                                 ChefDeployer=self.deploy_class, RackspaceCreate=self.create_class):
            r = Runner(options={})
            r.main(self.create_args + [ '--use-opscode-chef', '1'])

            call_args = self.create_command.execute.call_args_list[0][1]
            self.assertEquals(True, call_args.get("use_opscode_chef"))

    def test_create_with_use_opscode_chef_not_specified(self):
        with mock.patch.multiple("littlechef_rackspace.runner", RackspaceApi=self.api_class,
                                 ChefDeployer=self.deploy_class, RackspaceCreate=self.create_class):
            r = Runner(options={})
            r.main(self.create_args)

            call_args = self.create_command.execute.call_args_list[0][1]
            self.assertFalse("use_opscode_chef" in call_args)

    def test_create_with_networks_without_publicnet_raises_exception(self):
        with mock.patch.multiple("littlechef_rackspace.runner", RackspaceApi=self.api_class,
                                 ChefDeployer=self.deploy_class, RackspaceCreate=self.create_class):
            r = Runner(options={})
            with self.assertRaises(InvalidConfiguration) as cm:
                r.main(self.create_args + [ '--networks', 'abcdefg'])

            self.assertEquals('Must specify PublicNet in networks list (id=00000000-0000-0000-0000-000000000000)',
                              cm.exception.message)

    def test_create_with_networks_passes_networks(self):
        with mock.patch.multiple("littlechef_rackspace.runner", RackspaceApi=self.api_class,
                                 ChefDeployer=self.deploy_class, RackspaceCreate=self.create_class):
            r = Runner(options={})
            public_net_id = '00000000-0000-0000-0000-000000000000'
            custom_net_id= '45e8b288-3a98-4092-a3e8-37e2a540d004'
            r.main(self.create_args + [ '--networks', '{0},{1}'.format(public_net_id, custom_net_id)])

            call_args = self.create_command.execute.call_args_list[0][1]
            self.assertEquals([public_net_id, custom_net_id], call_args.get('networks'))
