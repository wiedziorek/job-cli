from .base import Base

class WriteShotgun(Base):
    """ Sub command which finds Shotgun project.
    """
    
    def run(self):
        """ Entry point for sub command.
        """
        from job.plugin import PluginManager
        manager = PluginManager(options=self.options)
        self.shotgun_writer = manager.get_plugin_by_name("ShotgunWriter")
        if self.shotgun_writer:
        	print self.shotgun_writer(self.options)
