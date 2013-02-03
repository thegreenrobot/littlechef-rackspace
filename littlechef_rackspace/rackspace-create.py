import sys
from lib import raise_error
from api import RackspaceApi, Regions
from deploy import ChefDeployer
from options import parser

(options, args) = parser.parse_args()

if not options.nodename:
    raise_error("must supply node name")
if not options.public_key:
    raise_error("must supply identity file")

if options.region.lower() == 'dfw':
    region = Regions.DFW
else:
    region = Regions.ORD

api = RackspaceApi(options.username, options.apikey, region)
host = api.create_node(node_name=options.nodename,
                       image_id=options.image,
                       flavor_id=options.flavor,
                       public_key_file=file(options.public_key),
                       progress=sys.stderr)
deployer = ChefDeployer(key_filename=options.private_key)

runlist = None
if options.roles:
    runlist = ['role[{0}]'.format(role) for role in options.roles.split(',')]

deployer.deploy(host, runlist)