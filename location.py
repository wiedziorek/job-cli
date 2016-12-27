import os
import stat
import json
from ordereddict import OrderedDict



class RenderedLocation(dict):
    """ This is basic database to propagete (render) all 
        information per directory. It is only used by
        workers to execute actual commands on disk or
        remote location. It's like a rendered flatten image of 
        all changes that will be performed.
    """
    parent = None
    def __init__(self, path, source, parent=None):
        """ This populates generated paths with common attributes.
        """
        self.parent = parent
        self['path'] = path
        self['permission']  = {'group': False, 'others': False}
        self['ownership']   = {'user' : None, 'group': 'artists'}
        self['is_link']     = False
        self['link_root']   = False
        self['link_target'] = None
        self['root']        = None

        # Parent copies settings first if provided:
        if parent:
            for k, v in parent.items():
                if k in self.keys():
                    self[k] = v

        # Then source otherrides if desired.
        for k, v in source.items():
            if k in self.keys():
                self[k] = v



class LocationTemplate(dict):
    """ This is tempate class reading settings per job AND per sub directory
        of an asset / shot. It keeps track to directory structure and permissions.
        It's main functionality is rendering templates into a list of RenderedLocation
        objects. It's also encapsulates some on-disk activities, although they should be
        probably moved to a specialized Device Object. 

        LocationTemplate takas 'schema', which is a directory of template's dictionaries
        provided by Job class and a 'obj', which is a name allowing to initilize it with 
        selected template.
    """
    schema  = {}
    parent  = None
    def __init__(self, schema, obj, parent=None, **kwargs):
        super(LocationTemplate, self).__init__(schema[obj])
        self.parent = parent
        for k, v in kwargs.items():
            self[k] = v

    def __getitem__(self, key):
        """ LocationTemplates are nested inside each othter. This custom getter
            looks for a key locally, and if not succeed, looks up the parents 
            recursively.
        """
        if key in self.keys():
            return super(LocationTemplate, self).__getitem__(key)
        else:
            # We are at a root level, and still no value... 
            if self.parent == None:
                raise KeyError, "No key found in self or parents: %s" % key
            return self.parent[key]


    def expand_path_template(self, template=None):
        """ This should be replaced with more elaboreted and safe template renderer. 
        """
        from os.path import join

        if not template:
            # This will raise an exception if no path_template has been found here
            # or up.
            template = self['path_template']

        consists = template.split("/")
        expanded_directores = []

        for element in consists:
            # all but first character is valid
            keyword = element[1:]
            if element.startswith("@"):
                # assert keyword in self.keys() # This won't work with nested 
                value = self[keyword]
            # We support also env var. which is probably bad idea...
            elif element.startswith("$"):
                value = os.getenv(keyword, None)
                assert value != None

            expanded_directores += [value]

        path = join(*expanded_directores)

        return path

    def render(self, _root=None, recursive=True, parent=None):
        """ Creates recursively LocationTemplate objects, resolving 
            overrides and expanding variables. 

            Returns: Dictonary with all paths as a keys, and coresponding
            templetes as values to use this information down the stream.
            {'/some/path': LocationTemplate(), ...}
        """
        from os.path import join, expandvars
        targets = OrderedDict()

        # If root wasn't provided take it from self or
        # regenerate it with path_template if avaible.
        if not _root or self['is_link']:
            template = self['path_template']
            root = self.expand_path_template(template)
        else:
            root = _root

        for name in self['names']:
            path = expandvars(join(root, name))
            targets[path] = self

        if not recursive:
            return 

        for sub_template in self['sub_dirs']:
            # Although the template was specified in a sub_dir
            # its definition is not in a path, so we omitt it.
            if not sub_template in self.schema.keys():
                continue

            location = LocationTemplate(self.schema, sub_template, parent=self)
            subtargets = location.render(path, parent=self)

            for tgk in subtargets:
                if tgk not in targets.keys():
                    targets[tgk] = subtargets[tgk]

        return targets


    def __repr__(self):
        """Pretty-like print with json rastezier."""
        return json.dumps(self, indent=4, check_circular=False)

    # http://stackoverflow.com/questions/16249440/changing-file-permission-in-python
    def remove_write_permissions(self, path):
        """Remove write permissions from this path, while keeping all other permissions intact.

        Params:
            path:  The path whose permissions to alter.
        """

        NO_USER_WRITING  = ~stat.S_IWUSR
        NO_GROUP_WRITING = ~stat.S_IWGRP
        NO_OTHER_WRITING = ~stat.S_IWOTH
        NO_WRITING = NO_USER_WRITING & NO_GROUP_WRITING & NO_OTHER_WRITING

        current_permissions = stat.S_IMODE(os.lstat(path).st_mode)
        os.chmod(path, current_permissions & NO_WRITING)

    def add_write_permissions(self, path, group=True, others=False):
        """ Set permissions flags according to provided params.

        Params:
            path:          The path to set permissions for.
            group, others: Permissions masks.
        """

        WRITING = stat.S_IWUSR 
        if group:
            WRITING = WRITING | stat.S_IWGRP
        if others:
            WRITING = WRITING | stat.S_IWOTH

        current_permissions = stat.S_IMODE(os.lstat(path).st_mode)
        os.chmod(path, current_permissions | WRITING)

    def set_ownership(self, path, user=None, group='artists'):
        """ Sets the ownership of a path. 

        Params:
            user:  User string (None means no change)
            group: Group string (default 'artists')
        """
        from grp import getgrnam
        from pwd import getpwnam, getpwuid
        from getpass import getuser
        
        if user:
            uid  = getpwnam(user).pw_uid
        else:
            uid =  os.stat(path).st_uid

        gid = getgrnam(group).gr_gid 
        os.chown(path, uid, gid)


    def load_schemas(self, path, schema={}):
        """Load *.json files defining Location objects. 
        """
        from glob import glob
        location = os.path.join(path, "*.json")
        files    = glob(location)

 
        for file in files:
            with open(file) as file_object:
                obj  = json.load(file_object)
                name = os.path.split(file)[1]
                name = os.path.splitext(name)[0]
                schema[name] = obj
        return schema



class Job(LocationTemplate):
    """ Hopfuly the only specialization of LocationTemplate class, 
        which provides functionality only for parent 'job' diretory.
        Main purpos of this class is to find and load all templates found
        in a paths (JOBB_PATH envvar.) It should also select in future
        Device Driver to operate on disk / remote server.

    """
    def __init__(self, jobb_path='JOBB_PATH', **kwargs):
        """ Initialize job by looking through JOBB_PATH locations and loading
            schema files from there. The later path in JOBB_PATH will override
            the former schames. 

            Note: Sub templates are created lazy on path rendering.
            job = Job() (no child templates created)
            job.render() (children createde recursively)
        """
        from os.path import join
        schema_locations = os.getenv(jobb_path, "./")
        schema_locations = schema_locations.split(":")

        for directory in schema_locations:
            schemas = self.load_schemas(join(directory, "schemas"))
            for k, v in schemas.items():
                self.schema[k] = v
        super(Job, self).__init__(self.schema, "job", **kwargs)

        # Asset diretory, as an exception, has no name
        self['names'] = [""]

    def make(self):
        """ TODO: This is only fo testing purposes.
        """
        def make_dir(path):
            if os.path.exists(path):
                print "Path exists: %s" % path
            try:
                os.makedirs(path)
            except:
                print "Couldn't make %s" %  path

        def make_link(path, targets):
            # ???
            parent = targets[path].parent
            assert parent != None
            # Find parent path by template object. 
            # TODO: Is it bug? There might be many parents paths?
            parent_path = targets.keys()[targets.values().index(parent)] 
            old_path, name = os.path.split(path)
            link_path = os.path.join(parent_path, name)
            try:
                os.symlink(path, link_path) 
            except:
                print "Can't make a link %s %s" % (path, link_path)

        targets = self.render()

        for path in targets:
            make_dir(path)
            if targets[path]['is_link']:
                make_link(path, targets)

            self.remove_write_permissions(path)
            self.add_write_permissions(path, **targets[path]['permission'])
            self.set_ownership(path, **targets[path]['ownership'])




if __name__ == "__main__":

    job = Job(job_name='sandbox', root='/tmp/dada')
   
    templates =  job.render()
    for template in templates:
        print template
    print job.make()
   
