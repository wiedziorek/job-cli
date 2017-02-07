from .base import BaseSubCommand

class WriteShotgun(BaseSubCommand):
    """ Sub command which finds Shotgun project.
    """
    
    def run(self):
        """ Entry point for sub command.
        """
        from job.plugin import PluginManager
        import plugins
        manager = PluginManager(options=self.cli_options)
        self.shotgun_writer = manager.get_plugin_by_name("ShotgunWriter")
        if self.shotgun_writer:
        	print self.shotgun_writer(self.options)
