import json
import os
import urllib2

from .recipe import HPB, Scripts


class ResourceNotFound(Exception):
    pass


class Source(object):
    def __init__(self):
        pass
    
    def categories(self):
        raise NotImplementedError

    def ports(self, category=None):
        raise NotImplementedError


class HaikuPortsWebsite(Source):
    #base_url = 'http://ports.haiku-files.org/future/bep'
    base_url = 'http://192.168.198.1/HaikuPorts-trac/bep'

    def __init__(self):
        pass
        
    def _get_data(self, url, list=False, meta=False):
    	if list:
    	    url += '/'
            if meta:
                url += '?meta'        
        url_file = urllib2.urlopen(url)
        return json.loads(url_file.read())

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
        url = self.base_url + '/' + category + '/'
        return self._get_data(url, meta)


class SVNRepository(Source):
    def __init__(self, path):
        self.path = path.rstrip(os.path.sep)
        
    def update(self):
        raise NotImplementedError
        
    def categories(self, meta=False):
        directories = os.walk(self.path).next()[1]
        directories.remove('.svn')
        if meta:
            directories = [{'name': directory} for directory in directories]
        return directories

    def ports(self, category='all', meta=False):
        ports = []
        for category in self.categories():
            directories = os.walk(self.path + os.path.sep + category).next()[1]
            directories.remove('.svn')
            if meta:
                ports += [{'name': directory, 'category': category}
                          for directory in directories]
            else:
                ports += list(directories)
        return ports

        
