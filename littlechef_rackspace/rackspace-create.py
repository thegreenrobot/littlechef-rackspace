import sys
from lib import raise_error, deploy_chef, save_node
from api import RackspaceApi, Regions
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
deploy_chef(options, host)
save_node(options, host)
