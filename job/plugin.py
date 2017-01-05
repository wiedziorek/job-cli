
class PluginTypes(object):
    device     = 0
    prefLoader = 1
    targetsPost= 2

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

        if not hasattr(self, 'plugins'):
            # Called when the metaclass is first instantiated
            self.plugins = []
        else:
            # Called when a plugin class is imported
            self.register_plugin(self)

    def register_plugin(self, plugin):
        """Add the plugin to the plugin list and perform any registration logic"""

        # create a plugin instance and store it
        # optionally you could just store the plugin class and lazily instantiate
        instance = plugin()

        # save the plugin reference
        self.plugins += [instance]

        # apply plugin logic - in this case connect the plugin to blinker signals
        # this must be defined in the derived class
        instance.register_signals()


class PluginManager(object):
    """A plugin which must provide a register_signals() method"""
    __metaclass__ = PluginRegister
    name = "PluginManager"
    type = None
    def __init__(self, *args, **kwargs):
        self.args   = args
        self.kwargs = kwargs
        super(PluginManager, self).__init__()

    def get_plugin_by_type(self, type):
        """
        """
        plg = []
        for plugin in self.plugins:
            if plugin.type == type:
                plg += [plugin]
        return plg

    def get_plugin_by_name(self, name):
        """
        """
        for plugin in self.plugins:
            if plugin.name == name:
                return plg

class MyPlugin(PluginManager):
    def register_signals(self):
        self.name = "MyPlugin"
        self.type = DEVICE_DRIVER
       
    def run(self):
        print "I can do other plugin stuff"


class MyPlugin2(PluginManager):
    def register_signals(self):
        self.name = "MyPlugin2"
        self.type = PREFERENCE_DRIVER

    def run(self):
        print "I can do other plugin stuff too"
        #print self.kwargs

context={'entry':"costamcostam"}
manager = PluginManager(context=context)

devices = manager.get_plugin_by_type(DEVICE_DRIVER)
for d in devices:
    d.run()