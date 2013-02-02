# Littlechef-Rackspace

Libraries for deploying chef to Rackspace Cloud Servers powered by OpenStack.
Meant to replace `knife rackspace` when a Chef Server is not in use.

Currently only supports creating a new server.

TODO: handle roles specified at the command line
TODO: rebuild a server

## Rackspace Create

```
python littlechef_rackspace/rackspace-create.py \
    -A <username> \
    -K <api_key> \
    --region (DFW|ORD)
    --image 5cebb13a-f783-4f8c-8058-c4182c724ccd \
    --flavor 2 \
    --node-name "test-creation"
    --public-key <public_key_file> (Used for bootstrapping)
    --private-key <private_key_file> (Used for bootstrapping)
```

The server is created with your public key file in the `/root/.ssh/authorized_keys`.
It is HIGHLY recommended that you disable root login as part of your chef recipes!