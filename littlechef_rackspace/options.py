from optparse import OptionParser

parser = OptionParser()
parser.add_option("-I", "--image", dest="image",
                  help="Image ID or name")
parser.add_option("-f", "--flavor", dest="flavor",
                  help="Flavor ID")
parser.add_option("-A", "--username", dest="username",
                  help="Rackspace Username")
parser.add_option("-N", "--node-name", dest="nodename",
                  help="Node name")
parser.add_option("-K", "--key", dest="apikey",
                  help="Rackspace API Key")
parser.add_option("-R", "--region", dest="region", default="",
                  help="Region for provisioning (required for OpenStack)")
parser.add_option("-a", "--public-key", dest="public_key",
                  help="Public Key File for Bootstrapping")
parser.add_option("-i", "--private-key", dest="private_key",
                  help="Private Key File for Bootstrapping")