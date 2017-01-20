# Import Job modules
from job.plugin import PluginManager, PluginType
from shotgun import ShotgunPlugin

class ShotgunReader(ShotgunPlugin, PluginManager):
    name = "ShotgunReader"
    type = PluginType.OptionWriter

    def read_asset(self, ha_project, ha_type, ha_asset, fields):
        sg_project = self.get_sg_project(ha_project)
        sg_type = self.get_sg_type(ha_type)
        filters = list()
        filters.append(["project", "is", sg_project])
        filters.append(["code", "is", ha_asset])
        return self.sg.find(sg_type, filters, fields)

    def read_type(self, ha_project, ha_type, fields):
        sg_project = self.get_sg_project(ha_project)
        sg_type = self.get_sg_type(ha_type)
        sg_asset_type = self.get_sg_asset_type(ha_type)
        filters = list()
        filters.append(["project", "is", sg_project])
        if sg_asset_type:
            filters.append(["sg_asset_type", "is", sg_asset_type])
        return self.sg.find(sg_type, filters, fields)

    def read_project(self, ha_project, fields):
        sg_project = self.get_sg_project(ha_project)
        filters = list()
        filters.append(["project", "is", sg_project])
        assets = self.sg.find("Asset", filters, fields)
        shots = self.sg.find("Shot", filters, fields)
        return assets + shots

    def __call__(self, options):
        if options["ASSET"]:
            return self.read_asset(options["PROJECT"],
                                   options["TYPE"],
                                   options["ASSET"],
                                   options["FIELDS"])
        elif options["TYPE"]:
            return self.read_type(options["PROJECT"],
                                  options["TYPE"],
                                  options["FIELDS"])
        else:
            return self.read_project(options["PROJECT"],
                                     options["FIELDS"])
