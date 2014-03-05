class Host(object):

    """
    Internal representation of a newly created/rebuilt server
    for Chef deployment, role addition, etc.
    """

    def __init__(self, name=None, host_string=None, ip_address=None, password=None, environment=None):
        self.name = name
        self.ip_address = ip_address
        self.password = password
        self.environment = environment

    def get_host_string(self):
        if self.name:
            return self.name

        return self.ip_address

    def __repr__(self):
        return '<Host name={0}, ip_address={1}, password={2}>'.format(
            self.name, self.ip_address, self.password
        )

    def __eq__(self, other):
        return (self.name == other.name and
                self.ip_address == other.ip_address and
                self.password == other.password and
                self.environment == other.environment)