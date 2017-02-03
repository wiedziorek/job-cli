from job.utils import ReadOnlyCacheAttrib, setup_logger

class PluginType(object):
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


        # FIXME!!! Clearly passing options (commandline) is not resolved now.
        # These are options:
        # 1. Somehow I feel, we should clearly separate level:
        #       a) ./bin/job command level passing user cli options to commands
        #       b) commands should prepare all options 'manually' and send to JobTemplates / 
        #          plugins only plain old python int/bools/vars, parsing all options by it self.
        # 2. Carry cli options docopt from object to object allowing commands and plugins to
        # use it as they like. This is fishy, since in case of changes in cli, all objects, and plugs
        # will have to accomodate to this.

        # FIXME:
        self.log_level = INFO
        if 'log_level' in self.kwargs:
            self.log_level = self.kwargs['log_level']
             
        self.logger = setup_logger("Plugin", log_level=self.log_level) # FIXME
        super(PluginManager, self).__init__()

    @property
    def plugins(self):
        return self._plugins_store

    @property
    def error(self):
        return self.last_error

    def get_plugin_by_type(self, type):
        """ Getter for plugins of type.

            Params: type -> class(type) present in job.plugin.PluginType.
            Return: List of matchnig plugins 
                    (classes derived from job.plugin.PluginManager) """
        plg = []
        for plugin in self.plugins:
            if plugin.type == type:
                plg += [plugin]
        return plg

    def get_plugin_by_name(self, name):
        """ Getter for plugin by name. Currently first matching name
         is returned, which might not be the best policy ever...

        Params: string prepresenting plugin class.
        Return: First matching plugin. """
        for plugin in self.plugins:
            if plugin.name == name:
                # FIXME: this is workaround...
                plugin.logger = setup_logger('Plugin', log_level=self.log_level)
                return plugin
