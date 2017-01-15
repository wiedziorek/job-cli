class ShotgunPlugin(object):

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

    def get_sg_asset_type(self, ha_type):
        if ha_type == "char":
            return "Character"
        elif ha_type == "prop":
            return "Prop"
        elif ha_type == "set":
            return "Environment"
        else:
            return None

    def get_sg_type(self, ha_type):
        if ha_type in ["char", "prop", "set"]:
            return "Asset"
        else:
            return "Shot"

    def get_sg_project(self, name):
        return self.sg.find_one("Project", [["name", "is", name]])

    def get_sg_asset(self, sg_project, sg_asset_type, code):
        filters = list()
        filters.append(["project", "is", sg_project])
        filters.append(["sg_asset_type", "is", sg_asset_type])
        filters.append(["code", "is", code])
        return self.sg.find("Asset", filters)

    def get_sg_sequence(self, project, code):
        filters = list()
        filters.append(["project", "is", project])
        filters.append(["code", "is", code])
        return self.sg.find("Sequence", filters)

    def get_sg_shot(self, project, sg_sequence, code):
        filters = list()
        filters.append(["project", "is", project])
        filters.append(["sg_sequence", "is", sg_sequence])
        filters.append(["code", "is", code])
        return self.sg.find("Shot", filters)
