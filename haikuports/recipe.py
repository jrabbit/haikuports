import os
from subprocess import check_call

from .parser import Parser, RequiredKey, OptionalKey, RequiredSelectKey, shell


class Recipe(object):
    def __init__(self, base_name, working_directory):
        self.base_name = base_name
        self.directory = working_directory

    def _run_script(self, script, env={}):
        # abort on first error
        script = ['set -e'] + script
        return check_call('\n'.join(script), shell=True,
                          cwd=self.directory, env=env)
    
    def build(self, script):
        return self._run_script(script)
    	
    def test(self, script):
        return self._run_script(script)
    	
    def install(self, script, target_directory):
        env = {'DESTDIR': target_directory}
        return self._run_script(script, env)

	def clean_work_directory(self):
	    raise NotImplementedError

    def set_flag(self, flag):
        filename = base_name + '.' + flag
        with file(filename, 'a'):
            os.utime(file)

    def check_flag(self, flag):
        filename = base_name + '.' + flag
        return os.path.exists(filename)


class HPB(Parser, Recipe):
    """Class representing a Haiku package builder recipe"""
    keys = {'DESCRIPTION': RequiredKey([str, list]),
            'HOMEPAGE': RequiredKey([str]),
            'SRC_URI': RequiredKey([str, list]),
            'STATUS_HAIKU': RequiredSelectKey(['untested', 'broken',
                                               'unstable', 'stable']),
            'DEPEND': OptionalKey([str, list, type(None)], None),
            'BUILD': RequiredKey([shell]),
            'INSTALL': RequiredKey([shell]),
            'LICENSE': RequiredKey([str, list]),
            
            # not yet supported by the portlog plugin
            'CHECKSUM_MD5': RequiredKey([str]),
            'TEST': OptionalKey([shell], None),
            'MESSAGE': OptionalKey([str], None),
            'COPYRIGHT': OptionalKey([str, list], None)
           }

    def __init__(self, filename, file):
    	super(HPB, self).__init__(filename, file)
    
    def validate(self, verbose=False):
        """Validate the keys"""
        super(HPB, self).validate(verbose)
        # verify key values...

    def build(self, directory):
        return super(HPB, self).build(self['BUILD'], directory)
    	
    def test(self, directory):
        return super(HPB, self).test(self['TEST'], directory)
    	
    def install(self, directory, target_directory):
        return super(HPB, self).test(self['INSTALL'], directory, target_directory)


class Scripts(Recipe):
    def __init__(self, path):
        self.path = path
 
 	def _read_script(self, script):
 	    return open(self.path + '.' + script).readlines()
        
    def build(self, directory):
        return super(Scripts, self).build(self._read_script('build'), directory)
    	
    def test(self, directory):
        return super(Scripts, self).test(self._read_script('test'), directory)
    	
    def install(self, directory, target_directory):
        return super(Scripts, self).install(self._read_script('install'), directory)


