from littlechef import runner as lc

from lib import raise_error, create_node, deploy_chef, save_node, get_conn
from options import parser


(options, args) = parser.parse_args()

if not options.nodename:
    raise_error("must supply node name")

conn = get_conn(options)
node = create_node(conn, name=options.nodename,
                   image=options.image, flavor=options.flavor)
node = deploy_chef(conn, node)
# TODO: add roles specified by the options
save_node(node)
