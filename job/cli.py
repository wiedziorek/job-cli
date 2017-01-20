import os
import stat
import json
import abc
import logging


# This will actually install optional plugins
# ... and crash on any error. We may hide it inside a class
# and catch exception, log etc. This should not hurt us,
# as pluggable functionality should be covered by built-in anyway.
# TODO: We should allow to import plugins from external module path
import plugins


# Python 2.6 compatibility:
try:
    from collections import OrderedDict, defaultdict
except ImportError:
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



class DeviceDriver(object):
    """ Abstract class defining an interface to production storage.
        Basic implementation does simply local storage manipulation via
        shell or Python interface. More interesitng implementations
        include remote execution or fuse virtual file systems.
    """
    __metaclass__ = abc.ABCMeta
    @abc.abstractmethod
    def make_dir(self, path):
        pass
    @abc.abstractmethod
    def make_link(self, path, targets):
        pass
    @abc.abstractmethod
    def remove_write_permissions(self, path):
        pass
    @abc.abstractmethod
    def add_write_permissions(self, path, group=True, others=False):
        pass
    @abc.abstractmethod
    def set_ownership(self, path, user=None, group=None):
        pass



class LocalDevice(DeviceDriver):
    logger = None
    def __init__(self, log_level=logging.INFO, **kwargs):
        super(LocalDevice, self).__init__(**kwargs)
        from .utils import setup_logger
        name = self.__class__.__name__
        self.logger = setup_logger(name, log_level=log_level)

    def make_dir(self, path):
        """ Uses standard Python facility to create a directory tree.
        """
        # TODO: How to process errors, 
        # TODO: How to implement more sofisticated error treatment
        # like: If path exists, and it's a link do A, if it's not a link do B?
        if os.path.exists(path):
            self.logger.warning("Path exists, can't proceed %s", path)
            return False
        # same as above.
        try:
            os.makedirs(path)
            self.logger.info("Making %s", path)
            return True
        except OSError, e:
            self.logger.exception("Couldn't make %s",  path)
            raise OSError

    def make_link(self, path, link_path):

        if os.path.exists(link_path):
            if os.path.islink(link_path):
                self.logger.warning("Link exists %s", link_path)
            else:
                self.logger.warning("Path exists, so I can't make a link here %s", link_path)
            return False

        try:
            os.symlink(path, link_path) 
            self.logger.info("Making symlink %s %s", path, link_path) 
            return True
        except:
            self.logger.exception("Can't make a link %s %s", path, link_path)
            raise OSError


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
        try:
            os.chmod(path, current_permissions & NO_WRITING)
        except:
            self.logger.exception("Can't remove write permission from %s", path)
            raise OSError

        self.logger.debug("remove_write_permissions: %s (%s)", path, current_permissions & NO_WRITING)

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

        try:
            os.chmod(path, current_permissions | WRITING)
        except:
            self.logger.exception("Can't add write permission for %s", path)
            raise OSError

        self.logger.debug("add_write_permissions: %s (%s)", path, current_permissions | WRITING)

    def set_ownership(self, path, user=None, group=None):
        """ Sets the ownership of a path. 

        Params:
            user:  User string (None means no change)
            group: Group string (None means no change)
        """
        from grp import getgrnam
        from pwd import getpwnam, getpwuid
        from getpass import getuser

        def get_user_id(path, user):
            """ """
            if not user:
                return os.stat(path).st_uid
            try: 
                return getpwnam(user).pw_uid
            except:
                self.logger.exception("Can't find specified user %s", user)
                raise OSError

        def get_group_id(path, group):
            """"""
            if not group:
                return os.stat(path).st_gid
            try: 
                return getgrnam(group).gr_gid 
            except:
                self.logger.exception("Can't find specified group %s", group)
                raise OSError

        # This may happen due to 'upper' logic...
        if not user and not group: 
            return False
        # 
        uid = get_user_id(path, user)
        gid = get_group_id(path, group)
        #
        try:
            os.chown(path, uid, gid)
        except:
            self.logger.exception("Can't change ownership for %s", path)
            raise OSError

        self.logger.debug("set_ownership: %s (%s, %s)", path, uid, gid)
        return True


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
    parent_template  = None
    schema_type_name = None
    child_templates  = []
    JOB_TEMPLATE_PATH_ENV = 'JOB_TEMPLATE_PATH' 
    SCHEMA_FILE_EXTENSION = "schema"
    OPTION_FILE_EXTENSION = "options"
    JOB_PATH_POSTFIX      = ["schema", ".job"]
    
    def __init__(self, schema=None, schema_type_name=None, parent=None, **kwargs):

        if schema and schema_type_name and schema_type_name in schema:
            super(LocationTemplate, self).__init__(schema[schema_type_name])

        self.parent_template = parent
        self.schema_type_name = schema_type_name

        # FIXME: This polutes schema as we save copies of self down the stream
        # This we should sanitaze kwargs here, so keys not present in schema
        # are saved separetly. We could also do it on saving. 
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
            if self.parent_template == None:
                raise KeyError, "No key found in self or parents: %s" % key
            return self.parent_template[key]

    def get_root_template(self):
        """ Return Job template which is a root parent.
        """
        if self.parent_template:
            return self.parent_template.get_root_template()
        return self


    def expand_path_template(self, template=None):
        """ This should be replaced with more elaboreted and safe template renderer. 
        """
        from os.path import join

        if not template:
            # This will raise an exception if 
            # no path_template has been found here or up.
            template = self['path_template']

        consists = template.split("/")
        expanded_directores = []

        for element in consists:
            # all but first character is valid
            keyword = element[1:]
            if element.startswith("@"): 
                value = self[keyword]
            # We support also env var. which is probably bad idea...
            elif element.startswith("$"):
                value = os.getenv(keyword, None)
            else: 
                value = element

            if not value:
                self.logger.exception("Couldn't resolve '%s' inside template: '%s'", \
                    element, template)
                raise EnvironmentError

            expanded_directores += [value]

        path = join(*expanded_directores)
        return path

    def extend_schema_with_adhoc_definition(self, schema_dict):
        """ LocationTemplate could be provided as simple sub_dirs
            inline. This should be used only for basic templates.
            By default all setting will be inherited from parent
            template. User can override it with "options" field
            inside inline template dictionary.

            Params: schema dictonary with three keys:
            { "name"   : location name
              "type"   : "location" for inline temp. or "template" for file based.
              "options": {} dict with overritten settings.
            }
        """

        schema = LocationTemplate(schema={}, 
                                  schema_type_name=None,
                                  parent=self)
        schema['sub_dirs'] = []
        if schema_dict['options']:
            for k, v in schema_dict['options'].items():
                schema[k] = v
        schema['names'] = [schema_dict['name']]
        self.schema[schema_dict['name']] = schema

        return True


    def render(self, _root=None, recursive=True, parent=None, clear_storage=True):
        """ Creates recursively LocationTemplate objects, resolving 
            overrides and expanding variables. 

            Returns: Dictonary with all paths as a keys, and coresponding
            templetes as values to use this information down the stream.
            {'/some/path': LocationTemplate(), ...}
        """
        def valid_variables_expantion(path):
            """ We need to make sure all var. were expanded, and raise
                an exception if not.
            """
            try:
                if '$' in path:
                    raise EnvironmentError(path)
            except EnvironmentError, e: 
                self.get_root_template().logger.exception("Wrong expansion %s", e)
                return False
            return True


        from os.path import join, expandvars
        from sys import exit

        targets = OrderedDict()

        if clear_storage:
            self.child_templates = []

        # If root wasn't provided take it from self or
        # regenerate it with path_template if avaible.
        if not _root or self['is_link']:
            template = self['path_template']
            root = self.expand_path_template(template)
        else:
            root = _root

        # print self.expand_path_template(self['link_target'])
        # Add paths to targets dictionary
        # We expand possible env variables and raise on error.
        for name in self['names']:
            path = join(root, name)
            path = expandvars(path)
            if not valid_variables_expantion(path):
                self.get_root_template().logger.info("Job has to quit due to errors...")
                exit()  
            targets[path] = self

        if not recursive:
            return 

        for sub_template in self['sub_dirs']:
            # Although the template was specified in a sub_dir
            # its definition can't be found, so we omitt it..
            if not sub_template['name'] in self.schema.keys() \
            and sub_template['type'] == "template":
                # print "Omitting absent template."
                continue

            # Expand schema shop (self.schema) inplace specification.
            if sub_template['type'] == "location":
                self.extend_schema_with_adhoc_definition(sub_template) 
                # print "Expanding schema with %s" % sub_template   

            # Create subtemplate and process...
            location = LocationTemplate(schema           = self.schema, 
                                        schema_type_name = sub_template['name'], 
                                        parent           = self)

            self.child_templates += [location]
            subtargets = location.render(path, parent=self)

            # FIXME: This shouldn't happen at all
            for tgk in subtargets:
                if tgk not in targets.keys():
                    targets[tgk] = subtargets[tgk]

        return targets


    def __repr__(self):
        """Pretty-like print with json rastezier."""
        return json.dumps(self, indent=4, check_circular=False)



    def load_schemas(self, path, schema={}):
        """Load json  schemas (*.schema) files defining LocationTemplates. 
        """
        from glob import glob
        location = os.path.join(path, "*.%s" % self.SCHEMA_FILE_EXTENSION)
        files    = glob(location)
        self.logger.debug("Schemas found: %s", files)

        for file in files:
            with open(file) as file_object:
                obj  = json.load(file_object)
                name = os.path.split(file)[1]
                name = os.path.splitext(name)[0]
                schema[name] = obj
        return schema



class JobTemplate(LocationTemplate):
    """ Hopefuly the only specialization of LocationTemplate class, 
        which provides functionality only for parent 'job' diretory.
        Main purpos of this class is to find and load all templates found
        in a paths (JOBB_PATH envvar.) It should also select in future
        Device Driver to operate on disk / remote server.

    """
    logger = None
    def __init__(self, log_level=logging.INFO, **kwargs):
        """ Initialize job by looking through JOBB_PATH locations and loading
            schema files from there. The later path in JOBB_PATH will override
            the former schames. 

            Note: Sub templates are created lazy on path rendering.
            job = Job() (no child templates created)
            job.render() (children created recursively)
        """
        from os.path import join, split, realpath, dirname
        from utils import setup_logger

        name = self.__class__.__name__
        self.logger = setup_logger(name, log_level=log_level)

        schema_locations  = [dirname(realpath(__file__))]

        # JOB_TEMPLATE_PATH_ENV may store store additional locations of schema folders.
        if os.getenv(self.JOB_TEMPLATE_PATH_ENV, None):
            schema_locations += os.getenv(self.JOB_TEMPLATE_PATH_ENV).split(":")

        self.logger.debug("schema_locations: %s", schema_locations)
        self.load_schemas(schema_locations)
        super(JobTemplate, self).__init__(self.schema, "job", **kwargs)

        # We make it pluggable since prefs/options might be
        # imported from database 
        from plugin import PluginManager 
        manager = PluginManager()

        self.options_reader = manager.get_plugin_by_name("FileOptionReader")
        self.logger.debug("Choosing option reader: %s", self.options_reader)

        # We oddly add options attrib to self here. 
        self.options = self.options_reader(self)
        if not self.options:
            self.logger.debug("Can't get options for a job! %s", self.options_reader.error)

    def get_local_schema_path(self):
        """ Once we know where to look for we may want to refer to
            local schema copy if the job/group/asset, as they might
            by edited independly from defualt schemas or any other
            present in environ varible JOB_TEMPLATE_PATH.

            Parms : job - object to retrieve local_schema_path templates.
            Return: list of additional schema locations. """
        # This is ugly, should we move it to Job()?
        job_schema   = self['local_schema_path']['job']
        group_schema = self['local_schema_path']['group']
        asset_schema = self['local_schema_path']['asset']

        local_schema_path  = [self.expand_path_template(template=job_schema)]
        local_schema_path += [self.expand_path_template(template=group_schema)]
        local_schema_path += [self.expand_path_template(template=asset_schema)]

        return local_schema_path

    def load_schemas(self, schema_locations):
        """ Loads schemas from files found in number of schema_locations/postix[s]
            as defined in JOB_PATH_POSTFIX global. """
        from os.path import join
        for directory in schema_locations:
            for postfix in self.JOB_PATH_POSTFIX:
                schemas = super(JobTemplate, self).load_schemas(join(directory, postfix))
                for k, v in schemas.items():
                    self.schema[k] = v
        return True

    def dump_local_templates(self, schema_key='job', postfix='.job'):
        """ Saves all schemes (hopefully) with modifications inside 
            path_template/postfix.

            Params: 
                schema_key: name of the path template used to generate prefix
                postfix:    subfolder to save *.json with schemas (usually .schema) 
        """
        def dumps_recursive(obj, objs, exclude_names={}):
            """ Puts strings containing json ready dicts recursively into obj. 
            """
            for tmpl in obj.child_templates:
                dumps_recursive(tmpl, objs, exclude_names)

            if obj.schema_type_name not in exclude_names:
                objs[obj.schema_type_name] = str(obj)

        def patch_local_schema(schema, local):
            """ Makes changes to schema based on local settings.
            """
            # TODO: Should it be recursive? 
            for key in schema:
                if key not in local:
                    continue
                if schema[key] == local[key]:
                    continue
                schema[key] = local[key]
                self.logger.warning("Patching schema key %s with %s.", key, local[key])
            return schema

        # TODO: Should we save schema' sources or recreate schames from objects?
        # Clear storage before rendering, so we make sure all possible changes in templates
        # (life objects opposite to shemas which are stored on disk.) will take effect. 
        tmpl_objects    = {}
        exclude_inlines = []
        targets = self.render(clear_storage=True).values()
        # FIXME: We need to keep track of inline templates... dirty. 
        for tmpl in targets:
            for inline in tmpl['sub_dirs']:
                if inline['type'] == 'location':
                    exclude_inlines += [inline['name']]

        # Local schemas path are defined in project's schema
        # and are selected here among many provided by key name: 
        local_schema_template = self['local_schema_path'][schema_key]

        prefix_path = self.expand_path_template(template=local_schema_template)
        prefix_path = os.path.join(prefix_path, postfix)
        prefix_path = os.path.expandvars(prefix_path)

        # FIXME: This shouldn't be here:
        if not os.path.isdir(prefix_path):
            self.logger.warning("Schema location doesn't exists! %s", prefix_path)
            try:
                os.mkdir(prefix_path)
                self.logger.info("Making local schema location %s", prefix_path)
            except:
                self.logger.exception("Can't make %s", prefix_path)


        # Patch schema with local settings:
        self.schema[self.schema_type_name] = \
        patch_local_schema(self.schema[self.schema_type_name], self)

        # get json-strings recursively:
        dumps_recursive(self, tmpl_objects, exclude_names=exclude_inlines)

        for schema in tmpl_objects:
            path = os.path.join(prefix_path, schema + ".%s" % self.SCHEMA_FILE_EXTENSION)
            with open(path, 'w') as file:
                file.write(tmpl_objects[schema])
                self.logger.debug("Saving schema: %s", path)

    def create(self):
        """ TODO: This is only fo testing purposes.
        """
        def create_link(path, targets):
            """ Create external or interal links between folders.

                'is_link' forces engine to override @root for
                particular target and link to a folder place as
                if @root wasn't overritten:

                    /@overritten_root/path --> /@original_root/path

                'link_target' does the opposite thing. It create link in remote
                place to our local target.

                   /@original_root/path --> /@overritten_root/path
            """

            if targets[path]['is_link']:
                # Remove it
                parent = targets[path].parent_template
                assert parent != None
                # Find parent path by template object. 
                parent_path    = targets.keys()[targets.values().index(parent)] 
                old_path, name = os.path.split(path)
                link_path      = os.path.join(parent_path, name)
                device.make_link(path, link_path)

            elif targets[path]['link_target']:
                if self['job_name'] == self['job_asset']:
                    return False 
                link_path = self.expand_path_template(targets[path]['link_target'])
                device.make_link(path, link_path)

            return True
            

        # TODO: Device driver should be pluggable
        device = LocalDevice(log_level=self.logger.level)
        device.logger.debug("Selecting device driver %s", device)
        targets = self.render()

        for path in targets:
            device.make_dir(path)
            create_link(path, targets)
            # Cosmetics:       
            device.remove_write_permissions(path)
            device.add_write_permissions(path, **targets[path]['permission'])
            device.set_ownership(path, **targets[path]['ownership'])
