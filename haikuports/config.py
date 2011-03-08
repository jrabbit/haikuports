import os

from .parser import Parser, OptionalKey


class Config(Parser):
    """Class representing the HaikuPorter configuration file"""
    keys = {'PACKAGES_PATH': OptionalKey([str], '/boot/develop/haikuports/repository'),
            'DOWNLOAD_PATH': OptionalKey([str], '/boot/develop/haikuports/download'),
            'BUILD_PATH': OptionalKey([str], '/boot/develop/haikuports/build'),
            'PATCH_OPTIONS': OptionalKey([str], '')
           }

    def __init__(self, filename, file):
    	super(Config, self).__init__(filename, file)
    	# remove trailing '/' from directory paths
    	for key, value in self.items():
    	    if key.endswith('_PATH'):
    	        self[key] = value.rstrip(os.path.sep)
