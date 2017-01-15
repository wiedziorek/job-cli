# Import Job modules
from job.plugin import PluginManager, PluginType
from shotgun import ShotgunPlugin

class ShotgunWriter(ShotgunPlugin, PluginManager):
    name = "ShotgunWriter"
    type = PluginType.OptionWriter

    def create_sg_asset(self, ha_project, ha_type, ha_asset):
        sg_project = self.get_sg_project(ha_project)
        sg_asset_type = self.get_sg_asset_type(ha_type)
        # Prevent Shotgun creating a second asset with identical name
        # in the given asset group.
        if self.get_sg_asset(sg_project, sg_asset_type, ha_asset):
            raise ValueError ("Asset already exists!")
        data = {
            "project": sg_project,
            "sg_asset_type": sg_asset_type,
            "code": ha_asset
        }
        return self.sg.create("Asset", data)

    def create_sg_shot(self, ha_project, ha_type, ha_asset):
        sg_project = self.get_sg_project(ha_project)
        sg_sequence = self.get_sg_sequence(sg_project, ha_type)
        if not sg_sequence:
            sg_sequence = self.create_sg_sequence(sg_project, ha_type)
        # Prevent Shotgun creating a second shot with identical name
        # in the given sequence.
        if self.get_sg_shot(sg_project, sg_sequence, ha_asset):
            raise ValueError ("Shot already exists!")
        data = {
            "project": sg_project,
            "sg_sequence": sg_sequence[0],
            "code": ha_asset
        }
        return self.sg.create("Shot", data)

    def create_sg_sequence(self, sg_project, code):
        data = {
            "project": sg_project,
            "code": code
        }
        return self.sg.create("Sequence", data)

    def create_sg_project(self, ha_project):
        data = {
            "name": ha_project,
            "sg_status": "Active"
        }
        return self.sg.create("Project", data)

    def __call__(self, options):
        if options["TYPE"]:
            if self.get_sg_type(options["TYPE"]) == "Asset":
                return self.create_sg_asset(options["PROJECT"],
                                            options["TYPE"],
                                            options["ASSET"])
            else:
                return self.create_sg_shot(options["PROJECT"],
                                           options["TYPE"],
                                           options["ASSET"])
        elif options["PROJECT"]:
            return self.create_sg_project(options["PROJECT"])
