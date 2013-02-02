from lib import raise_error, create_node, deploy_chef, save_node, get_conn
from options import parser

(options, args) = parser.parse_args()

if not options.nodename:
    raise_error("must supply node name")
if not options.public_key:
    raise_error("must supply identity file")

conn = get_conn(options)
node = create_node(conn, name=options.nodename,
                   image=options.image, flavor=options.flavor,
                   public_key=file(options.public_key).read())
node = deploy_chef(conn, node)
# TODO: add roles specified by the options
save_node(options.private_key, node)
