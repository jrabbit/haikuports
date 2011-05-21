import re
import sys


class Parser(dict):
    """"""
    # regular expressions for parsing the config file
    re_option_value = re.compile('^(?P<key>[A-Z0-9_]*)\s*='
                                 '\s*"(?P<value>.*)(?<!\\\\)"\s*$')
    re_option_list = re.compile('^(?P<key>[A-Z0-9_]*)\s*='
                                '\s*"(?P<item>.*)\s*$')
    re_last_list_item = re.compile('^\s+(?P<item>.*)(?<!\\\\)"\s*$')
    re_list_item = re.compile('^\s+(?P<item>.*)\s*$')
    re_shell_start = re.compile('^(?P<key>[A-Z_]*)\s*\{\s*(#.*)?$')
    re_shell_item = re.compile('^\t(?P<item>.*)\s*$')
    re_shell_end = re.compile('^\}\s*(#.*)?$')
    re_comment = re.compile('^\s*#.*$')
    re_empty_line = re.compile('^\s*$')
    re_none = re.compile('^\s*$')
    re_int = re.compile('^[0-9]+$')
    re_boolean = re.compile('^yes$|^no$')

    keys = {}
    defaults = {}
	
    def __init__(self, filename, file=None):
        self.filename = filename
        if file is None:
            return

        self.file = iter(file)
        self.line_count = 0
        
        line = self.next_line()
        # TODO: store all options in a list?
        try:
            while True:
                if self.re_empty_line.match(line)\
                     or self.re_comment.match(line):
                    pass
                elif self.re_option_value.match(line):
                    # print "[OV] " + line.strip('\n')
                    m = self.re_option_value.match(line)
                    key = m.group('key')
                    value = m.group('value')
                    if self.re_none.match(value):  # NoneType
                        self[key] = None
                    elif self.re_int.match(value):
                        self[key] = int(value)
                    elif self.re_boolean.match(value):
                        if value == 'yes':
                            self[key] = True
                        else:
                            self[key] = False
                    else:
                        self[key] = value
                elif self.re_option_list.match(line):
                    # print "[OL] " + line.strip('\n')
                    m = self.re_option_list.match(line)
                    key = m.group('key')
                    self[key] = [m.group('item')]
                    line = self.next_line()
                    while line != '':
                        if (self.re_empty_line.match(line) or
                            self.re_comment.match(line)):
                            pass
                        elif self.re_last_list_item.match(line):
                            # print "[LL] " + line.strip('\n')
                            m = self.re_last_list_item.match(line)
                            self[key].append(m.group('item'))
                            break
                        elif self.re_list_item.match(line):
                            # print "[LI] " + line.strip('\n')
                            m = self.re_list_item.match(line)
                            self[key].append(m.group('item'))
                        else:
                            self.illegal_syntax(line)
                        line = self.next_line()
                elif self.re_shell_start.match(line):
                    # print "[SS] " + line.strip('\n')
                    m = self.re_shell_start.match(line)
                    key = m.group('key')
                    self[key] = shell()
                    line = self.next_line()
                    while line != '':
                        if self.re_shell_end.match(line):
                            # print "[SE] " + line.strip('\n')
                            break
                        elif self.re_shell_item.match(line):
                            # print "[SI] " + line.strip('\n')
                            m = self.re_shell_item.match(line)
                            self[key].append(m.group('item') + '\n')
                        else:
                            self.illegal_syntax(line)
                        line = self.next_line()
                else:
                    self.illegal_syntax(line)
                line = self.next_line()
        except StopIteration:
            pass

        # for key in self:
        #     print key + " = " + str(self[key])

    def __missing__(self, key):
        """Return default value for non-specified key"""
        return self.keys[key].default

    def next_line(self):
        self.line_count = self.line_count + 1
        return next(self.file)

    def illegal_syntax(self, line):
        print 'Error: Illegal syntax in %s at line %d:' % (self.filename,
                                                           self.line_count)
        print '  ' + line
        sys.exit(1)

    def validate(self, verbose=False):
        """Validate the keys"""
        valid = True
        for name, key in self.keys.items():
            if key.required and name not in self:
                print("Error: Required field {0} not present "
                      "in {1}".format(name, self.filename))
                valid = False
        for key, value in self.items():
            try:
                if value not in self.keys[key].options:
                    print("Error: Unknown option '{0}' for {1} "
                          "in {2}".format(value, key, self.filename))
                    valid = False                	
            except KeyError:
                print("Error: Unknown field {0} in {1}".format(key,
                                                               self.filename))
                valid = False
            except AttributeError:
                pass
                
        return valid


# create new type for identifying lists of shell commands
class shell(list):
    pass


class Key(object):
    def __init__(self, types, required, default=None):
        self.types = types
        self.required = required
        self.default = default


class RequiredKey(Key):
    def __init__(self, types):
        super(RequiredKey, self).__init__(types, True)


class OptionalKey(Key):
    def __init__(self, types, default):
        super(OptionalKey, self).__init__(types, False, default)


class RequiredSelectKey(RequiredKey):
    def __init__(self, options):
        super(RequiredSelectKey, self).__init__([str])
        self.options = options
