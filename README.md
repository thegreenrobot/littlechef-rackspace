# Littlechef-Rackspace

Libraries for deploying chef to Rackspace Cloud Servers powered by OpenStack.
Meant to replace `knife rackspace` when a Chef Server is not in use.

Currently only supports creating a new server.

![Build Status](https://api.travis-ci.org/tildedave/littlechef-rackspace.png)]

Requires littlechef and libcloud.

```
pip install -r requirements.txt
```

* TODO: rebuild a server
* TODO: also look in littlechef config file for certain command line args
* TODO: set up install w/pip, validate that running scripts works in any littlechef kitchen

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
    --runlist "role[web],recipe[security-updates]"
```

The server is created with your public key file in the `/root/.ssh/authorized_keys`.
It is HIGHLY recommended that you disable root password login as part of your chef
recipes!

