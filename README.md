# Littlechef-Rackspace

[![Build Status](https://travis-ci.org/tildedave/littlechef-rackspace.png)](https://travis-ci.org/tildedave/littlechef-rackspace)

Libraries for deploying chef to Rackspace Cloud Servers powered by OpenStack.  Replaces `knife rackspace` when a Chef
Server is not in use.  Built on top of the excellent libcloud and littlechef libraries.

## Installation Instructions

```
pip install littlechef-rackspace
```

## Configuration

In order to perform any commands you must specify `username`, `key`, and `region`.

You can specify arguments on the command line or in your littlechef `config.cfg` file.  If you are making a large
number of machines that look 'the same' I recommend putting your image or flavor configuration in this file.  Your
`config.cfg` might look something like:

```
[userinfo]
user =
password =
keypair-file =
ssh-config = /home/dave/.ssh/config

[kitchen]
node_work_path = /tmp/chef-solo/

[rackspace]
secrets-file = secrets.cfg
image=5cebb13a-f783-4f8c-8058-c4182c724ccd
flavor=2
public_key=bootstrap.pub
private_key=bootstrap
region=dfw
environment=preprod
```

* `region`: Currently littlechef-rackspace supports Rackspace's Washington DC or Chicago datacenters (`dfw` or `ord`).

### Putting Your Secrets in a Secrets File

You can specify a `secrets-file` in the `config.cfg` that contains your username and api key.  This allows
your source repository to track common configuration (images, flavors) but not secrets.
Here's an example `secrets.cfg` file:

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
