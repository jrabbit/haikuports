# GPL v3 or MIT License.
# copyright 2011 Jack Laxson (Jrabbit)

import urlparse
import os
import urllib
import json
import re
from subprocess import PIPE, Popen, call

def parse_uri(uri):
    "take a uri and give file"
    parsed = urlparse.urlparse(uri)
    return os.path.split(parsed.path)[-1]

def parse_rev(f):
    "We're going to assume we can parse it, if we fail we ask the user."
    def is_version(s):
        for i in s.split('.'):
            if i.isdigit():
                pass
            else:
                return False
        return True

    pkg_name = f.split('-')[0]
    if '.tar.gz' in f:
        name, version = f.split('.tar.gz')[0].split('-')
    elif '.xz' in f:
        name, version = f.split('.xz')[0].split('-')[1]
    elif '.tar.bz2' in f:
        name, version = f.split('.tar.bz2')[0].split('-')[1]
    else:
        raise NameError
    if not is_version(version):
        raise ValueError
    else:
        return name, version


def what_category():
    "Where shall we place this lovely bep file?"
    categories_url = "http://ports.haiku-files.org/bep"
    categories = json.loads(urllib.urlopen(categories_url))
    print "Here are the haikuports categories:" 
    print categories
    print "Hints: dev-language is a good choice"
    desc = raw_input("Would you like descriptions? [Y/n] ")
    if desc in ['Y', 'y', '']:
        for cat in categories:
            l = json.loads(urllib.urlopen(categories_url+ cat))
            if l['description']:
                print l['name'] + " " + l['description']
    final_category == 'unchosen'
    while final_category == 'unchosen':
        choice = raw_input("Which best fits your package? ")
        if choice not in categories:
            print "I didn't quite get that right: %s" % choice
        else:
            final_category = choice
    return final_category
def checksum(uri):
    'Return \n or CHECKSUM_MD5="..."'
    if re.match('^cvs.*$|^svn.*$|^hg.*$|^git.*$|^bzr.*$',uri):
        return "\n"
    else:
        md5 = Popen(['wget', '-O -', uri, '|', 'md5sum'],stdout=PIPE, shell=True).communicate()[0]
        return 'CHECKSUM_MD5="%s"'% md5

    
def make_bep(name, category, version, uri):
    cat_loc = os.path.join(hp_tree, category, name)
    os.mkdir(cat_loc)
    bep_location = os.path.join(cat_loc, name+'-'+version+'.bep')
    bep = open(bep_location, w)
    skeleton = """SUMMARY="Short one line info."
    DESCRIPTION="Feed me Seymour! <Long info>" 
    HOMEPAGE="" 
    SRC_URI="%(uri)s"
    %(checksum)s
    REVISION="1"
    STATUS_HAIKU="broken"
    DEPEND=""
    PROVIDES=""
    BUILD_DEPEND="haiku-devel >= $haikuVersion"
    SOURCE_DIR="$portVersionedName"
    BUILD {
    	cd %(name_vers)s
    	make
    }

    INSTALL {
    	cd %(name_vers)s
    	make install
    }

    LICENSE="Refrence other packages for accepted Strings"
    COPYRIGHT="2011 Someone"
    """ % {'uri': uri, 'checksum': checksum(uri), 'name_vers': name+'-'+version }
    bep.write(skeleton)
    bep.close()
    return bep_location
def cat_error():
    "http://c2.com/cgi/wiki?AsciiKitten"
    return """  |\      _,,,---,,_
  /,`.-'`'    -.  ;-;;,_
 |,4-  ) )-,_..;\ (  `'-'
'---''(_/--'  `-'\_)    """
def create(url):
    #do stuff
    filename = parse_uri(url)
    try:
        name, version = parse_rev(filename)
    except (NameError, ValueError) as e:
            # Mention VCS urls.
            print cat_error()
            print "Something bad happened! I was not able to parse the url you gave me."
            print "It is possible you need to start again with haikuporter create git+http:/git/url or hg+http if you're intending to package from a VCS."
            name = raw_input("What is the pakage's name? ")
            version = raw_input("What version is it at? [If a vcs state the vcs name e.g.: hg, git] ")

    category = what_category()
    bep_location = make_bep(name, category, version, url)
    os.system('open ' +bep_location)

        