class Host(object):

    """
    Internal representation of a newly created/rebuilt server
    for Chef deployment, role addition, etc.
    """

    def __init__(self, name=None, host_string=None, password=None):
        self.name = name
        self.host_string = host_string
        self.password = password

    def __repr__(self):
        return '<Host name={0}, host_string={1}, password={2}>'.format(
            self.name, self.host_string, self.password
        )

    def __eq__(self, other):
        return (self.name == other.name and
                self.host_string == other.host_string and
                self.password == other.password)