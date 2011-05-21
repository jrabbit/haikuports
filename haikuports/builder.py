from optparse import OptionParser
import os
import re
import sys
from subprocess import check_call, CalledProcessError

from . import __version__
from .config import Config
from .source import HaikuPortsWebsite, SVNRepository, ResourceNotFound


class Builder(object):
    config_path = '/boot/common/etc/haikuports.conf'
    repository_path = 'http://ports.haiku-files.org/svn/haikuports/trunk'

    def __init__(self, options, arguments):
        self.config = Config(self.config_path)
        self.source = (SVNRepository(self.config)
                       if options.local else HaikuPortsWebsite(self.config))

        if options.get:
            self.update_ports_tree()
            return

        if options.list:
        	self.list_ports()
        elif options.about:
            self.about(arguments)
        elif options.search:
            self.search(arguments)
        elif len(arguments) == 0:
            print("You need to specifiy a port to build.\n"
                  "Invoke '{0} -h' for usage information.".format(sys.argv[0]))
        else:
            try:
                port, version_revision = arguments[0].split('-', 1)
                version, revision = version_revision.rsplit('-', 1)
                recipe = self.source.recipe(options, port, version, revision)

                if options.clean:
                    recipe.clean_build_directory()

                self.build(recipe)
            except ValueError:
                try: 
                    options = list(self.list_options(arguments[0]))
                    print('available options:')
                    for option in options:
                        print(' * {0}'.format(option))
                except ResourceNotFound as e:
                    print(e.msg)
            except ResourceNotFound as e:
                print(e.msg)

    def list_ports(self):
        for port in self.source.ports(meta=True):
        	print('{category}/{name}'.format(**port))
        
    def about(self, arguments):
        # TODO: generalize for ports, versions, revisions
        for port in arguments:
            try:
                metadata = self.source.port(port)
                output = '{name}'.format(**metadata)
                if metadata['description']:
                    output += ' - {description}'.format(**metadata)
                if metadata['homepage']:
                    output += '\n  {homepage}'.format(**metadata)
                if metadata['license']:
                    output += '\n  license: {license}'.format(**metadata)
                print(output)
            except ResourceNotFound as m:
                print(m)

    def update_ports_tree(self):
        """Get or update the ports tree via Subversion"""
        recipes_path = self.config['REPOSITORY_PATH']
        if os.path.exists(recipes_path + os.path.sep + '.svn'):
            print('Updating the HaikuPorts tree:')
            check_call(['svn', 'update', recipes_path])
        else:
            print('Checking out the HaikuPorts tree to '
                  '{0}'.format(recipes_path))
            check_call(['svn', 'checkout', self.repository_path, recipes_path])

    def search(self, arguments):
        """Search for a port in the HaikuPorts tree"""
        try:
            regex = re.compile(arguments[0])
            for name in self.source.ports(meta=False):
                if regex.search(name):
                    print('{category}/{name}'.format(**self.source.port(name)))
        except IndexError:
            print('You need to specifiy a search string.')
            print "Invoke '" + sys.argv[0] + " -h' for usage information."
            sys.exit(1)

    def list_options(self, string):
        try:
            port, ver_rev = string.split('-', 1)
            if not ver_rev:
                raise ValueError
            try:
                version, revision = ver_rev.rsplit('-', 1)
                if not revision:
                    raise ValueError
                if revision not in self.source.revisions(port, version):
                    raise ResourceNotFound('unknown revision: ' + revision)
                else:
                    yield None
            except ValueError:
                if ver_rev not in self.source.versions(port):
                    raise ResourceNotFound('unknown version: ' + ver_rev)
                else:
                    for revision in self.source.revisions(port, ver_rev):
                        yield port + '-' + ver_rev + '-' + str(revision)
        except ValueError:
            if string not in self.source.ports():
                raise ResourceNotFound('unknown port: ' + string)
            else:
                for version in self.source.versions(string):
                    yield string + '-' + version        

    def build(self, recipe):
        # TODO: move to Recipe.execute()?
        recipe.download()
        recipe.checksum()
        recipe.unpack()
        if recipe.options.patch:
            recipe.patch()
        if recipe.options.build:
            recipe.build()
        if recipe.options.test:
            recipe.test()
        if recipe.options.install:
            recipe.install()


def main():
   parser = OptionParser(usage='usage: %prog [options] '
                               'portname[-version[-revision]]',
                         version='%prog {0}'.format(__version__))

   parser.add_option('-r', '--repository', action='store_true', dest='local',
                     default=False, help='retrieve recipes from locally '
                                         'checked-out repostory instead of '
                                         'from the HaikuPorts website')

   parser.add_option('-l', '--list', action='store_true', dest='list',
                     default=False, help='list available ports')
   parser.add_option('-a', '--about', action='store_true', dest='about',
                     default=False, help='show description of the specified '
                                         'port')
   parser.add_option('-s', '--search', action='store_true', dest='search',
                     default=False, help='search for a port (regex)')
   parser.add_option('-p', '--nopatch', action='store_false', dest='patch',
                     default=True, help="don't patch the sources, just "
                                        "download and unpack")
   parser.add_option('-b', '--nobuild', action='store_false', dest='build',
                     default=True, help="don't build the port, just download, "
                                        "unpack and patch")
   parser.add_option('-i', '--install', action='store_true', dest='install',
                     default=False, help="also install the port (the default "
                                         "is to only build)")
#   parser.add_option('-d', '--distro', action='store_true', dest='distro',
#                     default=False, help="make distribution package of the "
#                                         "specified port (include download, "
#                                         "unpack, patch, build)")
   parser.add_option('-c', '--clean', action='store_true', dest='clean',
                     default=False, help="clean the working directory of the "
                                         "specified port")
   parser.add_option('-g', '--get', action='store_true', dest='get',
                     default=False, help="get/update the ports tree")
   parser.add_option('-f', '--force', action='store_true', dest='force',
                     default=False, help="force to perform the steps (unpack, "
                                         "patch, build)")
#   parser.add_option('-z', '--archive', action='store_true', dest='archive',
#                     default=False, help="Create a patched source archive as "
#                                         "<package>_haiku.tar.xz")
#   parser.add_option('-t', '--tree', action='store_true', dest='tree',
#                     default=False, help="print out the location of the "
#                                         "haikuports source tree")
   parser.add_option('-y', '--yes', action='store_true', dest='yes',
                     default=False, help="answer yes to all questions")

   parser.add_option('--test', action='store_true', dest='test',
                     default=False, help="run tests on resulting binaries")
#   parser.add_option('--lint', action='store_true', dest='lint',
#                     default=False, help="scan the ports tree for problems")

   (options, args) = parser.parse_args()
   builder = Builder(options, args)
