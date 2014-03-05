## 0.7 (alpha)

* Display performance flavors better (Samuel Toriel)
* Support creating IAD and HKG public cloud resources
* Add --dry-run argument for showing what arguments
  a node will be created with, but not actually executing
  the creation.
* Deprecate 'rackspace' section of config.cfg; LittleChef has deprecated
  the use of a config.cfg.  Future configuration for littlechef-rackspace
  should use rackspace.yaml.
* BREAKING: Remove 'hostname' argument.  Nodes are 
  created with the same hostname as their API name.

## 0.6 (2013-04-25)

* Support creating SYD resources (if your account has Sydney OpenStack
  enabled)

## 0.5 (2013-04-05)

* list-networks command to view custom networks on your account
* create command now takes a networks list
* Fixed regression introduced in 0.4 where not specifying opscode
  Chef would not deploy chef on new nodes

## 0.4 (2013-03-27)

* Python 2.6 support
* --skip-opscode-chef and --use-opscode-chef options to allow not using
  Opscode Chef Repositories on newly bootstrapped nodes

## 0.3 (2013-03-24)

* --hostname to create node file with specified hostname
* --plugins and --post-plugins for executing plugins before and after chef run

## 0.2 (2013-03-20)

* --environment to create nodes in a specific Chef Environment
* Fixed some errors in configuration parsing

## 0.1 (2013-02-05)

* Initial release, nothing works
