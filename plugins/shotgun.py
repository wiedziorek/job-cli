STUDIO_SGTK_PATH = "/STUDIO/sgtk/studio/install/core/python"

class ShotgunPlugin(object):
    logger = None
    def register_signals(self):
        import sys
        try:
            import sgtk
        except ImportError, e:
            sys.path.append(STUDIO_SGTK_PATH)
            try:
                import sgtk
            except:
                self.logger.debug("Cannot import sgtk, %s", e)
                return False

        self.logger.debug("%s registering as %s", self.name, self.type)

        # Create connection.
        self.sg = sgtk.util.shotgun.create_sg_connection()
        return True

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
