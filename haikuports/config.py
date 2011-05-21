import os

from .parser import Parser, OptionalKey


class Config(Parser):
    """Class representing the HaikuPorter configuration file"""
    keys = {'REPOSITORY_PATH': OptionalKey([str], '/boot/develop/haikuports/repository'),
            'DOWNLOAD_PATH': OptionalKey([str], '/boot/develop/haikuports/download'),
            'BUILD_PATH': OptionalKey([str], '/boot/develop/haikuports/build'),
            'PATCH_OPTIONS': OptionalKey([str], '')
           }

    def __init__(self, filename):
        if os.path.exists(filename):
            super(Config, self).__init__(filename,
                                         open(self.config_path).readlines())
        else:
            super(Config, self).__init__(filename)
    	# remove trailing '/' from directory paths
    	for key, value in self.items():
    	    if key.endswith('_PATH'):
    	        self[key] = value.rstrip(os.path.sep)
