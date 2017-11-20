import os


DEBUG = True


class PyVDriveConfiguration(object):
    """
    a singleton class used by
    """
    def __init__(self):
        """
        initialization
        """
        # define class
        self._infoDict = dict()

        # get the configuration file name
        config_dir = os.path.expanduser('~/.pyvdrive')
        self._configFileName = os.path.join(config_dir, 'PyVDriveConfig.config')

        # create the configuration file
        if os.path.exists(config_dir) is False:
            os.mkdir(config_dir)

        # check file
        if os.path.exists(self._configFileName):
            self.import_config(self._configFileName)

        else:
            self.init_config()

        return

    def init_config(self):
        """

        :return:
        """
        return

    def import_config(self, config_file_name):
        """
        import configuration file.
        this works under the assumption that the loading will be done during the
        initialization

        :param config_file_name:
        :return:
        """
        # check inputs
        assert isinstance(config_file_name, str), 'Configuration file must be string'
        if os.path.exists(config_file_name) is False:
            raise RuntimeError('Configuration file {0} cannot be found.'
                               ''.format(config_file_name))

        # import file
        config_file = open(config_file_name, 'r')
        lines = config_file.readline()
        config_file.close()

        for line in lines:
            line = line.strip()
            if len(line) == 0:
                continue

            items = line.split('=')
            self._infoDict[items[0]] = items[1]

        return

    def write_config(self):
        """
        write configuration file to the fixed one
        :return:
        """
        output_buffer = ''

        for key in self._infoDict:
            output_buffer += '{0} = {1}\n'.format(key, self._infoDict[key])

        # write
        config_file = open(self._configFileName, 'w')
        config_file.write(output_buffer)
        config_file.close()

        return
