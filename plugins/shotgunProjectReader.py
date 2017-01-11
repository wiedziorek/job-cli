# Import Job modules
from job.plugin import PluginManager, PluginType


class ShotgunProjectReader(PluginManager):
    name = "ShotgunProjectReader"
    type = PluginType.OptionReader

    def register_signals(self):
        print "I am %s and register as the %s" % (self.name, self.type)

    def find_project(self, name):
        # Import Shotgun Toolkit module
        import sys
        sgtk_path = "/STUDIO/sgtk/studio/install/core/python"
        if not sgtk_path in sys.path:
            sys.path.append(sgtk_path)
        import sgtk
        # Find project
        sg = sgtk.util.shotgun.create_sg_connection()
        project = sg.find_one("Project", [["name", "is", name]])
        return project

    def __call__(self, name):
        project = self.find_project(name)
        return project
