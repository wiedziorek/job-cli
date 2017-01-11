# Import Job modules
from job.plugin import PluginManager, PluginType

class ShotgunProjectReader(PluginManager):
    name = "ShotgunProjectReader"
    type = PluginType.OptionReader

    def __init__(self):
        # Import Shotgun Toolkit module.
        import sys
        sgtk_path = "/STUDIO/sgtk/studio/install/core/python"
        if not sgtk_path in sys.path:
            sys.path.append(sgtk_path)
        try:
            import sgtk
        except ImportError, e:
            print "Cannot import sgtk.", e
            raise ImportError
        # Create connection.
        self.sg = sgtk.util.shotgun.create_sg_connection()

    def register_signals(self):
        print "I am %s and register as the %s" % (self.name, self.type)

    def find(self, name, type, fields):
        project = self.sg.find_one("Project", [["name", "is", name]])
        return self.sg.find(type, [["project", "is", project]], fields)

    def __call__(self, options):
        if options["asset"]:
            type = "Asset"
        elif options["shot"]:
            type = "Shot"
        return self.find(options["PROJECT"], type, options["FIELDS"])
