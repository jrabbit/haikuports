from .parser import Parser, OptionalKey


class Config(Parser):
    """Class representing the HaikuPorter configuration file"""
    keys = {'PACKAGES_PATH': OptionalKey([str],
                                         '/boot/common/etc/haikuports.conf'),
            'PATCH_OPTIONS': OptionalKey([str], None)
           }

    def __init__(self, filename, file):
    	super(Config, self).__init__(filename, file)
