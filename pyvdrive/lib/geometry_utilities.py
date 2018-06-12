# A collection of methods and constants for VULCAN instrument geometry


class VulcanGeometry(object):
    """
    a static class to calculate vulcan geometry knowledge
    """
    def __init__(self, pre_ned=False):
        """
        initialization to define the type of VULCAN geometry
        :param pre_ned:
        """
        if pre_ned:
            self._generation = 1
        else:
            self._generation = 2

        return

    def 