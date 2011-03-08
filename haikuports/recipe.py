import os
import shutil
import sys
import tarfile
import urllib2
import zipfile

from subprocess import check_call, CalledProcessError

from .parser import Parser, RequiredKey, OptionalKey, RequiredSelectKey, shell


#def check_call(cmd, shell=True, env={}, cwd=''):
#   print cmd


class Recipe(object):
    def __init__(self, config, options, base_name):
        self.config = config
        self.options = options
        self.base_name = base_name
        self.download_directory = self.config['DOWNLOAD_PATH']
        self.build_directory = (self.config['BUILD_PATH'] + os.path.sep +
                                base_name)
        if not os.path.exists(self.build_directory):
            os.makedirs(self.build_directory)

    def _run_script(self, script, environment={}):
        env = os.environ
        env.update(environment)

        # abort on first error
        script = ['set -e\n'] + script
        try:
            return check_call(''.join(script), shell=True,
                              cwd=self.build_directory, env=env)
        except CalledProcessError:
            print('Error during script execution')
            sys.exit(1)

    def _message(self, msg):
        print('\033[1m' + msg + '...\033[0m')
    
    def retrieve_sources(self):
        raise NotImplementedError
        # download, checksum, unpack
        # or
        # checkout (cvs, svn, git, hg, bzr, ...)

    def download(self, url):
        self._message('Downloading archive')
        # get actual URL in case of http redirect
        url = urllib2.urlopen(url).geturl()
        
        self.archive = url.rsplit('/', 1)[1]
        target_dir = self.config['DOWNLOAD_PATH']
        if os.path.isfile(target_dir + os.path.sep + self.archive):
            print('File already exists: {0}\n'
                  'Skipping download ...'.format(self.archive))
        else:
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
            print('Downloading: {0}'.format(url))
            check_call(['wget', '-c', '--tries=3', '-P', target_dir, url],
                       cwd=self.download_directory)
    
    def checksum(self, archive, hash):
        raise NotImplementedError
    
    def unpack(self):
        """Unpack the source archive into the work directory"""
        if self.check_flag('unpack'):
            return

        self._message('Unpacking ' + self.archive)
        archive_path = self.download_directory + os.path.sep + self.archive
        if tarfile.is_tarfile(archive_path):
            tf = tarfile.open(archive_path)
            tf.extractall(self.build_directory)
            tf.close()
        elif zipfile.is_zipfile(archive_path):
            zf = zipfile.ZipFile(archive_path)
            zf.extractall(self.build_directory)
            zf.close()
        elif archive_path.rsplit('.', 1)[1] == 'xz':
            def unpack_xz():
                check_call(['xz', '-d', '-k', archive_path],
                           cwd=self.build_directory)

            try:
                unpack_xz()
            except (OSError, CalledProcessError), e:
                # run the installoptionalsoftware prompt
                if self.prompt_installer('xz'):
                    unpack_xz()
                else:
                    sys.exit()
            tar = archive_path[:-3]
            if tarfile.is_tarfile(tar):
                tf = tarfile.open(tar)
                tf.extractall(self.build_directory)
                tf.close()
        else:
            sys.exit('Error: Unrecognized archive type.')

        self.set_flag('unpack')
    
    def checkout(self, url):
        raise NotImplementedError
    
    def patch(self, patch):
        if not self.check_flag('patch'):
            check_call('patch -p0 -i {0}'.format(patch),
                       shell=True, cwd=self.build_directory)
            # TODO: check rc
            self.set_flag('patch')
    
    def build(self, script):
        self._message('Building')
        if not self.check_flag('build'):
            self._run_script(script)
            self.set_flag('build')
    	
    def test(self, script):
        self._message('Running tests')
        if not self.check_flag('test'):
            self._run_script(script)
            self.set_flag('test')
    	
    def install(self, script, target_directory):
        self._message('Installing to ' + target_directory)
        if not self.check_flag('install'):
            self._run_script(script, {'DESTDIR': target_directory})
            self.set_flag('install')

    def clean_build_directory(self):
	    self._message('Cleaning build directory')
	    shutil.rmtree(self.build_directory)

    def set_flag(self, flag):
        flag_path = self.build_directory + os.path.sep + flag
        with file(flag_path, 'w'):
            os.utime(flag_path, None)

    def check_flag(self, flag):
        flag_path = self.build_directory + os.path.sep + flag
        return not self.options.force and os.path.exists(flag_path)

    def prompt_installer(self, name):
        """Prompt the user to install an optional package"""
        apps = {'xz': 'XZ-Utils',
                'git': 'Git',
                'hg': 'mercurial',
                'cvs': 'cvs',
                'bzr': 'bazaar'}
        def do_install():
            return check_call(['installoptionalpackage', apps[name]], shell=True)       
         
        if self.options.yes:
            do_install()
            return True
        else:
            response = raw_input('Do you want to install %s? [Y/n]' % name)
            if response in ['y', 'Y', '\n', 'yes', '']:
                do_install()
                return True
            else:
                print ("In order to install this package you need to run "
                       "'installoptionalpackage {0}' manually or let "
                       "{1} install it for you.".format(apps[name],
                                                        sys.argv[0]))
                return False


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

    def __init__(self, config, options, filename, file):
    	super(HPB, self).__init__(filename, file)
    	Recipe.__init__(self, config, options, filename.rsplit('.', 1)[0])
    
    def validate(self, verbose=False):
        """Validate the keys"""
        super(HPB, self).validate(verbose)
        # verify key values...

    def download(self):
        return super(HPB, self).download(self['SRC_URI'])

    def patch(self):
        return
        patch_path = self.base_path + '.patch'
        if os.path.exists(patch_path):
        	return super(Scripts, self).patch(patch_path)
       	else:
       	    print('No patching required')

    def build(self):
        return super(HPB, self).build(self['BUILD'])
    	
    def test(self):
        return super(HPB, self).test(self['TEST'])
    	
    def install(self, target_directory):
        return super(HPB, self).test(self['INSTALL'], directory, target_directory)


class Scripts(HPB):
    """Identical to HPB, but fetch patch and scripts from the repository"""
    def __init__(self, config, options, filename, file, script_base_path):
        base_name = script_base_path.rsplit(os.path.sep, 1)[1]
        super(Scripts, self).__init__(config, options, filename, file)
        self.base_path = script_base_path
 
    def _read_script(self, script):
        return open(self.base_path + '.' + script).readlines()

    def patch(self):
        patch_path = self.base_path + '.patch'
        if os.path.exists(patch_path):
        	return Recipe.patch(self, patch_path)
       	else:
       	    print('No patching required')

    def build(self):
        return Recipe.build(self, self._read_script('build'))
    	
    def test(self):
        return Recipe.test(self, self._read_script('test'))
    	
    def install(self, target_directory):
        return Recipe.install(self, self._read_script('install'))


