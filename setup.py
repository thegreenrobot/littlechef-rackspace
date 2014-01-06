try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name="littlechef-rackspace",
    version=__import__('littlechef_rackspace').__version__,
    description="Scripts for bootstrapping Rackspace Cloud Servers with Littlechef",
    author="Dave King",
    author_email="tildedave@gmail.com",
    url="http://github.com/tildedave/littlechef-rackspace",
    download_url="http://github.com/tildedave/littlechef-rackspace/archives/master",
    keywords=["chef", "rackspace", "openstack", "devops", "operations"],
    install_requires=['littlechef>=1.4.1', 'apache-libcloud==0.12.4'],
    packages=['littlechef_rackspace'],
    scripts=['fix-rackspace'],
    test_suite='nose.collector',
    classifiers=[
        "Programming Language :: Python",
        "Environment :: Console",
        "Intended Audience :: Developers",
        ],
    long_description="""\
Deploy Chef to Rackspace Cloud Servers without a chef server.  Replaces
knife-rackspace for users of littlechef.

.. _Chef: http://wiki.opscode.com/display/chef/Home
.. _LittleChef: https://github.com/tobami/littlechef
.. _Rackspace Cloud Servers: http://www.rackspace.com/cloud/servers/
"""
)
