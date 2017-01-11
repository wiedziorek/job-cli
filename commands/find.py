from .base import Base

class FindShotgunProject(Base):
    """ Sub command which finds Shotgun project.
    """
    
    def run(self):
        """ Entry point for sub command.
        """
        from job.plugin import PluginManager
        manager = PluginManager()
        self.shotgun_reader = manager.get_plugin_by_name("ShotgunProjectReader")
        print self.shotgun_reader(self.options)
