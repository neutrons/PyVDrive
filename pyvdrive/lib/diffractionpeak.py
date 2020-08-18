__author__ = 'wzz'


class DiffractionPeak:
    """
    Class to describe a diffraction peak including its type and peak parameters
    """

    def __init__(self, profile):
        """ Initialize peak profile parameters
        :return:
        """
        assert isinstance(profile, str)

        self._profileType = profile
        self._centre = None
        self._intensity = None
        self._fwhm = None

    @property
    def centre(self):
        """ Get peak centre
        :return:
        """
        return self._centre

    @centre.setter
    def centre(self, value):
        """
        Set value to centre
        :param value:
        :return:
        """
        assert value > 0.
        self._centre = value

        return

    @property
    def intensity(self):
        """ Get peak intensity
        :return:
        """
        return self._intensity

    @intensity.setter
    def intensity(self, value):
        """ Set peak intensity
        :param value:
        :return:
        """
        assert value > 0.
        self._intensity = value

    @property
    def width(self):
        """ Get peak width (FWHM)
        :return:
        """
        return self._fwhm

    @width.setter
    def width(self, value):
        """ Set peak's width
        :param value:
        :return:
        """
        assert value > 0.
        self._fwhm = value
