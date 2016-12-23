#!/usr/bin/python

# template = """{% for target in targets %}
#     $JOB/{{ target.url }} permission flag: {{ target.permission }} link to -->\
#     None{{ target.linkto }}{% endfor %}

# """

# from jinja2 import Template
# t = Template(template)

# targets = {"targets": [{'url': 'camera', 'permission': 077, 'linkto':None },
#            {'url': 'geo', 'permission': 077, 'linkto':None }]}

# print t.render(targets)

import os
import stat
import json

class Location(dict):
    def __init__(self, source=None, **kwargs):
        super(Location, self).__init__()

        if source:
            for k, v in source.items():
                self[k] = v
        else:
            self['root']        = '/PROD/dev'
            self['job_name']    = "sandbox"
            self['job_group']   = "user"
            self['job_asset']   = "$USER"
            self['permission']  = ['']
            # self['']
            self['is_link']     = False
            self['link_target'] = None
            self['link_root']   = None
            self['user_dirs']   = False
            self['names']       = []
            self['sub_dirs']    = {}

        for k, v in kwargs.items():
            self[k] = v

    def is_link(self):
        return self['is_link']

    def render(self, _root=None, recursive=True):
        """ Returns a list of path created by this object along with
            possible subdirectories.
        """
        paths = []
        from os.path import join, expandvars
        # if self._names: else ""

        if not _root:
            root = self['root']
            root = expandvars(join(root, self['job_name'], \
                self['job_group'], self['job_asset']))
        else:
            root = _root 

        for name in self['names']:
            path = expandvars(join(root, name))
            paths += [path]

        if not recursive:
            return paths

        for subpath in self['sub_dirs']:
            assert subpath in globals()
            obj = globals()[subpath]()
            paths += obj.render(path)
        return paths

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


class Camera(Location):
    def __init__(self, source=None, **kwargs):
        super(Camera, self).__init__(source, **kwargs)
        if not source:
            self['names']      = ["camera"]
            self['sub_dirs']   = {'CameraFormats':""}

class CameraFormats(Location):
    def __init__(self, source=None, **kwargs):
        super(CameraFormats, self).__init__(source, **kwargs)
        self['names'] = ['abc', 'json', 'chan']

class Render(Location):
    def __init__(self, source=None, **kwargs):
        super(Render, self).__init__(source, **kwargs)
        self['names'] = ['render']
        self['user_dirs'] = True
        self['sub_dirs']  = {'RenderFormats': ""}

class RenderFormats(Location):
    def __init__(self, source=None, **kwargs):
        super(RenderFormats, self).__init__(source, **kwargs)
        self['names'] = ['mantra', 'nuke', 'afx']




# camera = Camera()
# # print camera.is_link()
# print camera.render(recursive=True)
# print Render().render()
# print Render()


