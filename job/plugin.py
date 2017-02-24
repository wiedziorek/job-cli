##########################################################################
#
#  Copyright (c) 2017, Human Ark Animation Studio. All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#
#     * Neither the name of Human Ark Animation Studio nor the names of any
#       other contributors to this software may be used to endorse or
#       promote products derived from this software without specific prior
#       written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
#  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
#  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
#  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
#  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
##########################################################################

from job.utils import ReadOnlyCacheAttrib, CachedMethod

# In time we would probably make from it own big module, but for now it's 
# OK to leave it here, as I suppose. PluginType is just enumerator, then we should have
# an abstract class for every type of it. Finally we have two classes responsible for
# initialization pluggins and providing them to consumers.

class PluginType(object):
    """ Enumeration for plugin types.
        Nothing fancy atm (placeholder).
    """
    class DeviceDriver(type):
        pass
    class OptionReader(type):
        pass
    class OptionWriter(type):
        pass
    class PreTempateRenderAction(type):
        pass
    class PostRenderTempalateAction(type):
        pass
    class Environment(type):
        pass


class DeviceDriver():
    """ Abstract class defining an interface to production storage.
        Basic implementation does simply local storage manipulation via
        shell or Python interface. More interesitng implementations
        include remote execution or fuse virtual file systems.
    """
    # __metaclass__ conflicts with current plugin architecture.
    # TODO: Reconsider changing one of it (plugins arch)
    # __metaclass__ = abc.ABCMeta
    # @abc.abstractmethod
    def make_dir(self, path):
        raise NotImplementedError('You must implement this method yourself!')
    # @abc.abstractmethod
    def make_link(self, path, targets):
        raise NotImplementedError('You must implement this method yourself!')
    # @abc.abstractmethod
    def remove_write_permissions(self, path):
        raise NotImplementedError('You must implement this method yourself!')
    # @abc.abstractmethod
    def add_write_permissions(self, path, group=True, others=False):
        raise NotImplementedError('You must implement this method yourself!')
    # @abc.abstractmethod
    def set_ownership(self, path, user=None, group=None):
        raise NotImplementedError('You must implement this method yourself!')


class Environment():
    """ Abstract class defining an interface to define job environment.
        Current implentation uses rez to create on-the-fly package per set command
        and saves it in user/.job folder for later reuse. In other words setting on
        shot or asset means creating or openingn previosly created rez pachage. 
        This was we can model environment with whole rez infrastructure. We might end up
        in something else. Thus pluggable version or environment resolving.
    """
    def find_context(self, **kwargs):
        raise NotImplementedError('You must implement this method yourself!')
   
    def create_context(self, **kwargs):
        raise NotImplementedError('You must implement this method yourself!')

    def execute_context(self, **kwargs):
        raise NotImplementedError('You must implement this method yourself!')

    @property
    def context_name(self, **kwargs):
        raise NotImplementedError('You must implement this method yourself!')


class DatabaseDriver():
    """ Abstrat class definig an interface for reading project data
        from external database.
    """
    type = PluginType.OptionReader
    def read_project(self, **kwargs):
        raise NotImplementedError('You must implement this method yourself!')

    def read_asset(self, **kwargs):
        raise NotImplementedError('You must implement this method yourself!')


class PluginRegister(type):
    """
    A plugin mount point derived from:
        http://martyalchin.com/2008/jan/10/simple-plugin-framework/
    Acts as a metaclass which creates anything inheriting from Plugin
    # see http://stackoverflow.com/questions/14510286/plugin-architecture-\
    # plugin-manager-vs-inspecting-from-plugins-import
    """

    def __init__(self, name, bases, attrs):
        """Called when a Plugin derived class is imported"""

        if not hasattr(self, '_plugins_store'):
            # Called when the metaclass is first instantiated
            self._plugins_store = []
        else:
            # Called when a plugin class is imported
            self.register_plugin(self)

    def register_plugin(self, plugin):
        """Add the plugin to the plugin list and perform any registration logic"""

        # create a plugin instance and store it
        # optionally you could just store the plugin class and lazily instantiate
        instance = plugin()

        # apply plugin logic - in this case connect the plugin to blinker signals
        # this must be defined in the derived class
        if instance.register_signals():
            # save the plugin reference
            self._plugins_store += [instance]




class PluginManager(object):
    """A plugin which must provide a register_signals() method"""
    __metaclass__ = PluginRegister
    name = "PluginManager"
    type = None
    def __init__(self, *args, **kwargs):
        from job.utils import get_log_level_from_options
        from logging import INFO, DEBUG
        self.args   = args
        self.kwargs = kwargs
        self.last_error = None
        self.last_info  = None
        self.cli_options= None

        # FIXME:
        self.log_level = INFO
        if 'log_level' in self.kwargs:
            self.log_level = self.kwargs['log_level']

        from job.logger import LoggerFactory   
        self.logger = LoggerFactory().get_logger("PluginManager", level="INFO") # FIXME
        super(PluginManager, self).__init__()

    @property
    def plugins(self):
        return self._plugins_store

    @property
    def error(self):
        return self.last_error

    @CachedMethod
    def get_plugin_by_type(self, type):
        """ Getter for plugins of type.

            Params: type -> class(type) present in job.plugin.PluginType.
            Return: List of matchnig plugins 
                    (classes derived from job.plugin.PluginManager) """
        from job.logger import LoggerFactory
        plg = []
        for plugin in self.plugins:
            if plugin.type == type:
                plugin.logger = LoggerFactory().get_logger(plugin.name, level=self.log_level)
                plg += [plugin]
        return plg

    @CachedMethod
    def get_plugin_by_name(self, name):
        """ Getter for plugin by name. Currently first matching name
         is returned, which might not be the best policy ever...

        Params: string prepresenting plugin class.
        Return: First matching plugin. 
        """
        from job.logger import LoggerFactory
        for plugin in self.plugins:
            if plugin.name == name:
                # FIXME: this is workaround...
                plugin.logger = LoggerFactory().get_logger(name, level=self.log_level)
                return plugin
        self.logger.exception("Can't find plugin %s", name)
        raise OSError

    # @CachedMethod
    def get_first_maching_plugin(self, prefered_plugin_names):
        """ Select first matching plugin from provided list of names.

        Params: List with prefered plugins names.
        Return: First matching plugin. 
        """
        from collections import Iterable
        from job.logger  import LoggerFactory
        
        assert isinstance(prefered_plugin_names, Iterable)
        installed_plg_names = [plugin.name for plugin in self.plugins]
        for plugin_name in prefered_plugin_names:
            if plugin_name in installed_plg_names:
                plugin_instance = self.get_plugin_by_name(plugin_name)
                # FIXME: this is workaround...
                plugin_instance.logger  = LoggerFactory().get_logger(plugin_name,\
                    level=self.log_level)
                return plugin_instance
        return None