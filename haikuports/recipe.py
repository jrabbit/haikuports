import hashlib
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
        except KeyboardInterrupt:
            print('Aborted by user')
            sys.exit(0)

    def _message(self, msg):
        print('\033[1m' + msg + '...\033[0m')
    
    def _error(self, msg, rc=1):
        print('\033[31mError:\033[0m ' + msg)
        sys.exit(rc)

    def cook(self):
        if 'MESSAGE' in self:
            self._message('Message')
            if self['MESSAGE']:
                print self['MESSAGE']
                if not self.options.yes:
                    answer = raw_input('Continue (y/n + enter)? ')
                    if answer == '':
                        sys.exit(1)
                    elif answer[0].lower() == 'y':
                        print ' ok'
                    else:
                        sys.exit(1)

        self.download()
        self.checksum()
        self.unpack()
        if self.options.patch:
            self.patch()
        if self.options.build:
            self.build()
        if self.options.test:
            self.test()
        if self.options.install:
            self.install()

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
        self.archive_path = self.download_directory + os.path.sep + self.archive
        if os.path.isfile(self.archive_path):
            print('File already exists: {0}\n'
                  'Skipping download ...'.format(self.archive))
        else:
            if not os.path.exists(self.download_directory):
                os.makedirs(self.download_directory)
            print('Downloading: {0}'.format(url))
            check_call(['wget', '-c', '--tries=3', '-P',
                        self.download_directory, url])
    
    def checksum(self, reference):
        self._message('Verifying checksum')
        hash = hashlib.md5()
        archive = open(self.archive_path, 'rb')
        while True:
            buffer = archive.read(16384)
            if not buffer:
                break
            hash.update(buffer)
        archive.close()
        if hash.hexdigest() == reference.lower():
            print('OK')
        else:
            print('FAILED\n'
                  ' Expected: {0}\n'
                  ' Found: {1}'.format(reference, hash.hexdigest()))
            sys.exit(1)
    
    def unpack(self):
        """Unpack the source archive into the work directory"""
        if self.check_flag('unpack'):
            return

        self._message('Unpacking ' + self.archive)
        
        if tarfile.is_tarfile(self.archive_path):
            tf = tarfile.open(self.archive_path)
            tf.extractall(self.build_directory)
            tf.close()
        elif zipfile.is_zipfile(self.archive_path):
            zf = zipfile.ZipFile(self.archive_path)
            zf.extractall(self.build_directory)
            zf.close()
        elif self.archive_path.rsplit('.', 1)[1] == 'xz':
            def unpack_xz():
                check_call(['xz', '-d', '-k', self.archive_path],
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
        self._message('Patching')
        if not self.check_flag('patch'):
            check_call('patch -p0 -i {0}'.format(patch),
                       shell=True, cwd=self.build_directory)
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

    def install(self, script):
        self._message('Installing')
        if not self.check_flag('install'):
            self._run_script(script)
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

            'PORTREV_DESCRIPTION': RequiredKey([str, list]),
            'MESSAGE': OptionalKey([str, list], None),
            'STATUS_HAIKU': RequiredSelectKey(['untested', 'broken',
                                               'unstable', 'stable']),
            'DEPEND': OptionalKey([str, list, type(None)], None),
            'BUILD': RequiredKey([shell]),
            'INSTALL': RequiredKey([shell]),
            'LICENSE': RequiredKey([str, list]),
            
            'CHECKSUM_MD5': RequiredKey([str]),
            'TEST': OptionalKey([shell], None),

            # not yet supported by the portlog plugin
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
        if 'SRC_URI' not in self:
            self._error('no sources URL given in recipe')
        return super(HPB, self).download(self['SRC_URI'])

    def checksum(self):
        reference = self['CHECKSUM_MD5']
        if not reference:
            self._message('No checksum provided in recipe')
        else:
            super(HPB, self).checksum(reference)

    def patch(self):
        if 'PATCH' in self:
            patch_path = (self.build_directory + os.sep +
                          self.base_name + '.patch')
            patch_file = open(patch_path, 'w')
            patch_file.writelines(self['PATCH'])
            patch_file.close()
            return super(HPB, self).patch(patch_path)
        else:
            self._message('No patching required')

    def build(self):
        return super(HPB, self).build(self['BUILD'])

    def test(self):
        return super(HPB, self).test(self['TEST'])

    def install(self):
        return super(HPB, self).test(self['INSTALL'])


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

    def install(self):
        return Recipe.install(self, self._read_script('install'))


