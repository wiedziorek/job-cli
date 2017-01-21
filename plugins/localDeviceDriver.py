from job.plugin import PluginManager, PluginType
from deviceDriver import DeviceDriver
from job.utils import setup_logger
from logging import INFO
import os, stat

class LocalDevicePython(DeviceDriver, PluginManager):
    name = "LocalDevicePython"
    type = PluginType.DeviceDriver
    logger = None

    def __init__(self, log_level=INFO, **kwargs):
        name = self.__class__
        self.log_level = log_level
        # super(LocalDevicePython, self).__init__(**kwargs)
        # PluginManager.__init__(self, **kwargs)
        # from .utils import setup_logger
        self.logger = setup_logger('LocalDevice', log_level=self.log_level)

    def register_signals(self):
        self.logger.debug("Registering LocalDevicePython")
        return True
        

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