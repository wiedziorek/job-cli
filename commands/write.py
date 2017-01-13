from .base import Base

class WriteShotgun(Base):
    """ Sub command which finds Shotgun project.
    """
    
    def run(self):
        """ Entry point for sub command.
        """
        from job.plugin import PluginManager
        manager = PluginManager()
        self.shotgun_writer = manager.get_plugin_by_name("ShotgunWriter")
        print self.shotgun_writer(self.options)
