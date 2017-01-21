from .base import BaseSubCommand

class ReadShotgun(BaseSubCommand):
    """ Sub command which finds Shotgun project.
    """
    
    def run(self):
        """ Entry point for sub command.
        """
        from job.plugin import PluginManager
        manager = PluginManager(options=self.cli_options)
        self.shotgun_reader = manager.get_plugin_by_name("ShotgunReader")
        if self.shotgun_reader:
        	print self.shotgun_reader(self.options)
        else:
        	print "Can't get shotgun_reader"
