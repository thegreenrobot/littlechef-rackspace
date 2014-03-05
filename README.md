# Littlechef-Rackspace

[![Build Status](https://travis-ci.org/tildedave/littlechef-rackspace.png)](https://travis-ci.org/tildedave/littlechef-rackspace)

Deploy chef to Rackspace Cloud Servers powered by OpenStack without a Chef Server.

Replaces `knife rackspace` for users of LittleChef.

Built on top of the excellent [libcloud](http://libcloud.org/) and [littlechef](https://github.com/tobami/littlechef) libraries.

## Installation Instructions

You must have libyaml-dev installed (C library required by PyYAML).

```
pip install littlechef-rackspace
```

## Configuration

`littlechef-rackspace` supports a number of commands for managing your Cloud Resources.

* create
* list-images
* list-networks
* list-flavors

To do any of these, commands you must specify `username`, `key`, and `region`.

You can specify arguments on the command-line or in a `rackspace.yaml` file.x
Your `rackspace.yaml` might look something like:

```yaml
secrets-file: secrets.cfg
image: 5cebb13a-f783-4f8c-8058-c4182c724ccd
flavor: 2
public_key: bootstrap.pub
private_key: bootstrap
region: dfw
environment: preprod
```

* `region`: You can choose any Rackspace Cloud region (DFW, ORD, IAD,
  SYD, LON, HKG).  For LON servers you must have an enabled account (sign up
  at rackspace.co.uk).

### Putting Your Secrets in a Secrets File

You can specify a `secrets-file` in the `rackspace.yaml` that contains your username and api key.
This allows your source repository to track common configuration (images, flavors) but not secrets.
The `secrets.cfg` file is a Python configuration file and secrets will be read from under the
`[DEFAULT]` configuration section. Here's an example `secrets.cfg` file:

```
[DEFAULT]
username=myrackspaceusername
key=myrackspaceapikey
```

## Rackspace Create

```
fix-rackspace create \
    --username <username> \
    --key <api_key> \
    --region <region, must be DFW or ORD> \
    --image 5cebb13a-f783-4f8c-8058-c4182c724ccd \
    --flavor 2 \
    --node-name "test-creation" \
    --public-key <public_key_file> \
    --private-key <private_key_file> \
    --runlist "role[web],recipe[security-updates]" \
    --plugins "save_network,save_cloud" \
    --post-plugins "mark_node_as_ready" \
    --hostname "test.example.com"
```

### Arguments

* `image`: Image to use (e.g. Ubuntu 12.04)
* `flavor`: Flavor to use (e.g. 2GB, 4GB, 8GB)
* `node-name`: Name of the newly created node in the Rackspace Cloud Control panel.  Also sets the initial
  hostname.
* `hostname`: Host name of the newly created node.  This only sets the name of created node JSON file.  You will
  need to set up DNS and set the hostname on the machine yourself.
* `public_key`: Public key used to authorize root SSH access
* `private_key`: Private key used to authenticate as root to the newly created node
* `environment`: Sets the `chef_environment` on a newly created node
* `runlist`: Comma separated list of the Chef runlist to execute on the node.
* `plugins`: Comma separated list of littlechef plugins.  Plugins are executed after chef deploy but
  before your recipe run.  If your recipes depend on the `cloud` attribute being set, you can specify a custom
  littlechef `save_cloud` plugin that uses ohai to save data to the node before your cookbooks are run.
* `post-plugins`: Comma separated list of littlechef plugins.  These plugins are executed after the initial
  chef run.  They can be used to mark that a node is ready to go into rotation (for example).
* `skip-opscode-chef`: Don't run `deploy_chef` to install chef with opscode packages (only on command line)
* `use-opscode-chef`: '0' or '1' based on whether to run `deploy_chef` after initial node startup (defaults to 1).
  Useful when you are installing your own chef packages through a plugin.

### Templates

In practice many arguments are grouped together for creates.  For example, you may have a staging install in the DFW datacenter, but a production install in the ORD datacenter.  These datacenters all use different private network identifiers.  Additionally, you may have several types of node: web, application server, database, each with different plugins or runlists.

To support this hierarchy in arguments and reduce "what were those arguments anyways?" syndrome, `littlechef-rackspace` supports _templates_.  These are specified in your rackspace.yml.

```yaml
templates:
  base:
    runlist:
      - recipe[test]
      - recipe[test2]
  web:
    runlist:
      - recipe[web]
  preprod:
    region: dfw
    environment: preprod
    networks:
      - 00000000-0000-0000-0000-000000000000
      - 3d443c50-a45e-11e3-a5e2-0800200c9a66
  production:
    region: ord
    environment: production
    networks:
      - 00000000-0000-0000-0000-000000000000
      - 5df00920-a45e-11e3-a5e2-0800200c9a66
```

Once a template is defined you can use it as part of node creation by specifying it after the 'create'.

```
# Applies 'web' and 'preprod' templates to new node 'web-n01.preprod'
fix-rackspace create --name web-n01.preprod web preprod

# Applies 'web' and 'production' templates to new node 'web-n01.prod'
fix-rackspace create --name web-n01.prod web production
```

### Notes

The server is created with your public key file in the `/root/.ssh/authorized_keys`.
I highly recommended that you disable root password login as part of your chef
recipes!

## Rackspace List Images

List the images with your associated region.  Handy for finding the image you want to create.

```
$ fix-rackspace list-images
bca91446-e60e-42e7-9e39-0582e7e20fb9       Fedora 16 (Verne)
17282573-81b3-4a2d-80e4-7fcf16d4ac08       Windows Server 2012 (with updates) + SQL Server 2012 Web SP1
a620e9ee-cd4c-47a0-b909-042cb5058488       Windows Server 2012 (with updates) + SQL Server 2012 Standard SP1
3071dff8-6564-481e-a9c0-2c67f0b8cbf0       Windows Server 2012 (with updates)
# etc
```

## Rackspace List Flavors

```
$ fix-rackspace list-flavors
2         512MB Standard Instance
3         1GB Standard Instance
4         2GB Standard Instance
5         4GB Standard Instance
6         8GB Standard Instance
7         15GB Standard Instance
8         30GB Standard Instance
```

## Tips for OS X

Mac users will most likely encounter the following libcloud error:

```
No CA Certificates were found in CA_CERTS_PATH
```

This can be remedied by executing the following:

```
$ brew install curl-ca-bundle
$ export SSL_CERT_FILE=/usr/local/opt/curl-ca-bundle/share/ca-bundle.crt
```

More information about this error can be found at [libcloud.apache.org](http://libcloud.apache.org/docs/ssl-certificate-validation.html)
