from .base import BaseSubCommand

class ReadShotgun(BaseSubCommand):
    """ Sub command which finds Shotgun project.
    """
    
    def run(self):
        """ Entry point for sub command.
        """
        from job.plugin import PluginManager
        import plugins
        manager = PluginManager(self.cli_options)
        self.shotgun_reader = manager.get_plugin_by_name("ShotgunReader")
        if not self.shotgun_reader:
            return

        self.shotgun_reader(self.cli_options)
        project_items = self.shotgun_reader.read_project_items(self.cli_options['PROJECT'])
        for item in project_items:
        	print item
        