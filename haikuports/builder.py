from optparse import OptionParser
import re
import sys

from . import __version__
from .config import Config
from .source import HaikuPortsWebsite, SVNRepository, ResourceNotFound


class Builder(object):
    config_path = '/boot/common/etc/haikuports.conf'

    def __init__(self, options, arguments):
        self.config = Config(self.config_path,
                             open(self.config_path).readlines())
        self.source = (SVNRepository(self.config['PACKAGES_PATH'])
                       if options.local else HaikuPortsWebsite())
        if options.list:
        	self.list_ports()
        elif options.about:
            self.about(arguments)
        elif options.search:
            self.search(arguments)
        else:
            self.build(options, arguments)
        
    def list_ports(self):
        for port in self.source.ports(meta=True):
        	print('{category}/{name}'.format(**port))
        
    def about(self, arguments):
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

    def build(self, options, arguments):
        port = arguments[0]
        if options.patch:
            self.source.port(port).patch()
        if options.build:
            self.source.port(port).build()
        if options.install:
            self.source.port(port).install()
	    pass


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
#   parser.add_option('-c', '--clean', action='store_true', dest='clean',
#                     default=False, help="clean the working directory of the "
#                                         "specified port")
#   parser.add_option('-g', '--get', action='store_true', dest='get',
#                     default=False, help="get/update the ports tree")
#   parser.add_option('-f', '--force', action='store_true', dest='force',
#                     default=False, help="force to perform the steps (unpack, "
#                                         "patch, build)")
#   parser.add_option('-z', '--archive', action='store_true', dest='archive',
#                     default=False, help="Create a patched source archive as "
#                                         "<package>_haiku.tar.xz")
#   parser.add_option('-t', '--tree', action='store_true', dest='tree',
#                     default=False, help="print out the location of the "
#                                         "haikuports source tree")
#   parser.add_option('-y', '--yes', action='store_true', dest='yes',
#                     default=False, help="answer yes to all questions")

#   parser.add_option('--test', action='store_true', dest='test',
#                     default=False, help="run tests on resulting binaries")
#   parser.add_option('--lint', action='store_true', dest='lint',
#                     default=False, help="scan the ports tree for problems")

   (options, args) = parser.parse_args()
   builder = Builder(options, args)
