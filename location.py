import os
import stat
import json


class RenderedLocation(dict):
    """ This is basic database to propagete (render) all 
        information per directory. It is only used by
        workers to execute actual commands on disk or
        remote location. It's like a rendered flatten image of 
        all changes that will be performed.
    """
    def __init__(self, path, source, parent=None):
        """ This populates generated paths with common attributes.
        """
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
    schema = {}
    def __init__(self, schema, obj, **kwargs):
        super(LocationTemplate, self).__init__(schema[obj])
    
        for k, v in kwargs.items():
            self[k] = v


    def expand_path_template(self, template=None, replace_dir=None):
        """ This should be replaced with more elaboreted and safe template renderer. 
        """
        from os.path import join

        if not template:
            if  'path_template' in self.keys():
                template = self['path_template']
            else:
                raise Exception, "No template found at %s" % str(self)

        consists = template.split("/")
        expanded_directores = []

        for element in consists:
            # all but first character is valid
            keyword = element[1:]
            if element.startswith("@"):
                # We allow arbitrary element replacement via provided dictionary. 
                if keyword in replace_dir:
                    print "replacing " + keyword, 
                    keyword = replace_dir[keyword]
                    print keyword
                assert keyword in self.keys()
                value = self[keyword]
            # We support also env var. which is probably bad idea...
            elif element.startswith("$"):
                value = os.getenv(keyword, None)
                assert value != None

            expanded_directores += [value]

        path = join(*expanded_directores)

        return path

    def render(self, _root=None, recursive=True, parent=None):
        """ Returns a list of path created by this object along with
            possible subdirectories.
        """
        from os.path import join, expandvars

        renders = []
        replace_dir = {}

        if self['link_root']:
            replace_dir = {'root': 'link_root'}
            self['is_link'] = True

        # If root wasn't provided take it from self or
        # regenerate it with path_template if avaible.
        if not _root or self['link_root']:
            if "path_template" in self.keys():
                root = self.expand_path_template(self['path_template'], replace_dir=replace_dir)
            else:
                root = self['link_root'] if self['is_link'] else self['root']
                # Expands env vars and use default structure.
                # This is fall back to default studio structure:
                root = expandvars(join(root, self['job_name'], \
                    self['job_group'], self['job_asset']))
        else:
            root = _root


        for name in self['names']:
            path = expandvars(join(root, name))
            details = RenderedLocation(path, self, parent)
            renders += [details]

        if not recursive:
            return paths

        for subpath in self['sub_dirs']:
            # Although the template was specified in a sub_dir
            # its definition is not in a path, so we omitt it.
            if not subpath in self.schema.keys():
                continue

            location = LocationTemplate(self.schema, subpath)
            _paths = location.render(path, parent=self)
            for p in _paths:
                if p not in renders:
                    renders += [p]

        return renders

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

        paths_to_create = self.render()
        for details in paths_to_create:
            if os.path.exists(details['path']):
                print "Path exists: %s" % details['path']
                continue
            try:
                os.makedirs( details['path'])
            except:
                print "Couldn't make %s" %  details['path']

        for details in paths_to_create:   

            self.remove_write_permissions(details['path'])
            self.add_write_permissions(details['path'], **details['permission'])
            self.set_ownership(details['path'], **details['ownership'])




if __name__ == "__main__":

    job = Job(job_name='sandbox', root='/tmp/dada')
   
    templates =  job.render()
    for template in templates:
        print template
    #print job.make()
   
