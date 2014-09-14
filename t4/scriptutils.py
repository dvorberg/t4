import sys, os, os.path as op, re, shlex, ConfigParser

class RCSyntaxError(Exception): pass

class config_file(object):
    """
    A config file using shell-like syntax convaining field=value pairs.
    Field names will be attribute names of on object of this class.
    """
    def __init__(self, filename=None):
        if filename is None:
            self.filename = ".%src" % op.basename(sys.argv[0])
        else:
            self.filename = filename

        self.config_parser = ConfigParser.ConfigParser()
            
        home = os.getenv("HOME")
        rcfile_name = op.join(home, self.filename)
        if op.exists(rcfile_name):
            self.config_parser.read(rcfile_name)

    def __getattr__(self, name):
        try:
            return self.config_parser.get("options", name)
        except ( ConfigParser.NoOptionError, ConfigParser.NoSectionError, ):
            return None

class configuration(object):
    """
    Model the configuration of a script. Takes a readily configured
    option parser as first argument, lets it parse the command line
    arguments and stores options and arguments as attributes.

    An object of this class will act like the options object created
    by an argparser, except that it will return values from the config
    file.

    After parsing both, command line options and the config file, the
    validate() method will be called which does nothing by default but
    allows you to report option errors back to the user.

    All options default to None.
    """
    def __init__(self, argparser, config_file=None):
        self.argparser = argparser
        self.arguments = argparser.parse_args()
        self.config_file = config_file
        self.validate()

    def __getattr__(self, name):
        ret = getattr(self.arguments, name, None)
        if ret is not None:
            return ret
        else:
            return getattr(self.config_file, name, None)

    def error(self, message):
        """
        To be used from within validate(): Call error() on the parser,
        that is: report the error on the terminal and quit the script
        gracefully.
        """
        self.parser.error(message)
        
    def validate(self):
        pass
