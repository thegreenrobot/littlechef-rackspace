import unittest
import mock
from littlechef_rackspace.api import Regions, RackspaceApi
from littlechef_rackspace.commands import RackspaceCreate, RackspaceListImages
from littlechef_rackspace.deploy import ChefDeployer
from littlechef_rackspace.runner import Runner, MissingRequiredArguments, InvalidConfiguration, InvalidCommand

class RunnerTest(unittest.TestCase):

    def setUp(self):
        self.api_class = mock.Mock(spec=RackspaceApi)
        self.rackspace_api = self.api_class.return_value
        self.deploy_class = mock.Mock(spec=ChefDeployer)
        self.chef_deployer = self.deploy_class.return_value
        self.create_class = mock.Mock(spec=RackspaceCreate)
        self.create_class.name = 'create'

        self.create_command = self.create_class.return_value
        self.list_images_class = mock.Mock(spec=RackspaceListImages)
        self.list_images_class.name = 'list-images'

        self.list_images_command = self.list_images_class.return_value

        # Dumb hacks using README.md as a public key because you can't mock out a file() call
        self.create_args = "create --flavor 2 --image 123 --node-name test-node --username username --key deadbeef --region dfw --public-key README.md".split(' ')
        self.list_images_args = "list-images --username username --key deadbeef --region dfw --public-key README.md".split(' ')

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
                                 ChefDeployer=self.deploy_class, RackspaceListImages=self.list_images_class),\
             self.assertRaises(InvalidConfiguration):
            r = Runner(options={})
            r.main(["list-images"])

    def test_list_images_instantiates_api(self):
        with mock.patch.multiple("littlechef_rackspace.runner", RackspaceApi=self.api_class,
                                 ChefDeployer=self.deploy_class, RackspaceListImages=self.list_images_class):
            r = Runner(options={})
            r.main(self.list_images_args)
            self.api_class.assert_any_call(username="username", key="deadbeef", region=Regions.DFW)

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
        with self.assertRaises(InvalidConfiguration):
            r.main(["create"])

    def test_create_fails_if_required_arguments_are_not_provided(self):
        with self.assertRaises(MissingRequiredArguments):
            r = Runner(options={})
            self.create_command.validate_args.return_value = False
            r.main("create --username username --key deadbeef --region dfw".split(" "))

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
