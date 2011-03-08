import glob
import json
import os
import urllib2

from .recipe import HPB, Scripts


class ResourceNotFound(Exception):
    def __init__(self, message):
        self.msg = message


class Source(object):
    def __init__(self, config):
        self.config = config
    
    def categories(self):
        raise NotImplementedError

    def ports(self, category=None):
        raise NotImplementedError

    def port(self, name):
        raise NotImplementedError
    
    def recipe(self, port, version, revision):
        raise NotImplementedError


class ConnectionError(Exception):
    """Raised when the HaikuPorts website cannot be reached"""
    pass


class HaikuPortsWebsite(Source):
    base_url = 'http://ports.haiku-files.org/future/bep'
    #base_url = 'http://192.168.198.1/HaikuPorts-trac/bep'
    extension = '.bep'

    def __init__(self, config):
        super(HaikuPortsWebsite, self).__init__(config)
        
    def _get_data(self, url, list=False, meta=False):
    	if list:
    	    url += '/'
            if meta:
                url += '?meta'
        try:
            url_file = urllib2.urlopen(url)
            return json.loads(url_file.read())
        except urllib2.URLError:
            raise ConnectionError

    def categories(self, meta=False):
        url = self.base_url + '/'
        return self._get_data(url, meta)

    def ports(self, category='all', meta=False):
        url = self.base_url + '/' + category
        ports = self._get_data(url, True, meta)
        if meta:
            ports.sort(key=lambda x: x['category'])
        else:
            ports.sort()
        return ports
        
    def port(self, name):
        url = self.base_url + '/' + 'all' + '/' + name
       	try:
        	return self._get_data(url)
        except urllib2.HTTPError:
        	raise ResourceNotFound("port '{0}' not found".format(name))

    def versions(self, port):
        url = self.base_url + '/all/' + port + '/'
        return self._get_data(url)

    def revisions(self, port, version):
        url = self.base_url + '/all/' + port + '/' + version + '/'
        return self._get_data(url)

    @classmethod
    def _fetch_recipe(cls, port, version, revision):
        filename = '-'.join([port, version, revision]) + cls.extension
        url = '/'.join([cls.base_url, 'all', port, version, revision])
        try:
            url_file = urllib2.urlopen(url)
            return filename, url_file.readlines()
        except urllib2.HTTPError:
            raise ResourceNotFound('port {0}-{1}-{2} '
                                   'not found'.format(port, version, revision))

    def recipe(self, options, port, version, revision):
        filename, recipe = self._fetch_recipe(port, version, revision)
        return HPB(self.config, options, filename, recipe)


class SVNRepository(Source):
    def __init__(self, config):
        super(SVNRepository, self).__init__(config)
        self.path = self.config['PACKAGES_PATH']
    
    def update(self):
        raise NotImplementedError
        
    def categories(self, meta=False):
        directories = os.walk(self.path).next()[1]
        directories.remove('.svn')
        for directory in directories:
            yield {'name': directory} if meta else directory

    def ports(self, category='all', meta=False):
        for category in self.categories():
            directories = os.walk(self.path + os.path.sep + category).next()[1]
            directories.remove('.svn')
            for port in directories:
                if meta:
                    yield {'name': port, 'category': category}
                else:
                    yield port

    def port(self, name):
        for port in self.ports(meta=True):
            if port['name'] == name:
                return port
        raise ResourceNotFound("port '{0}' not found".format(name))

    def _port_base(self, port_name):
        port = self.port(port_name)
        return ('{base}{sep}{category}{sep}{port}{sep}'
                '{port}'.format(base=self.path, category=port['category'],
                                port=port['name'], sep=os.path.sep))

    def versions(self, port_name):
        base_path = self._port_base(port_name)
        for path in glob.glob('{0}-*-*.build'.format(base_path)):
            script = path.rsplit(os.path.sep, 1)[1]
            yield script.split('-', 1)[1].rsplit('-', 1)[0]

    def revisions(self, port_name, version):
        base_path = self._port_base(port_name)
        for script in glob.glob('{0}-{1}-*.build'.format(base_path, version)):
            yield script.rsplit('-', 1)[1].rsplit('.', 1)[0]

    def recipe(self, options, port, version, revision):
        filename, recipe = HaikuPortsWebsite._fetch_recipe(port, version, revision)
        script_base_path = ('{port_base}-{version}-{revision}'
                            .format(port_base=self._port_base(port),
                                    version=version, revision=revision,
                                    sep=os.path.sep))
        if not os.path.exists(script_base_path + '.build'):
            raise ResourceNotFound('port {0}-{1}-{2} '
                                   'not found'.format(port, version, revision))
        return Scripts(self.config, options, filename, recipe, script_base_path)
