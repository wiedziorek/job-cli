# Import Job modules
from job.plugin import PluginManager, PluginType, DatabaseDriver
from shotgun import ShotgunPlugin


class ShotgunReader(ShotgunPlugin, DatabaseDriver, PluginManager):
    name = "ShotgunReader"
    # Type specified in DatabaseDriver as OptionReader
    def get_asset_fields(self):
        """ Get all fields used by Shotgun to describe an Asset entity

        :returns:           A list of Shotgun field names
        """
        schema = self.sg.schema_field_read('Asset')
        fields = schema.keys()
        return sorted(fields)

    def get_shot_fields(self):
        """ Get all fields used by Shotgun to describe a Shot entity

        :returns:           A list of Shotgun field names
        """
        schema = self.sg.schema_field_read('Shot')
        fields = schema.keys()
        return sorted(fields)

    def read_asset(self, project, asset_type, asset_name, fields=None):
        """ Get values of Shotgun fields on a given shot or asset. By default,
        information on id, code, type, and either sg_sequence or sg_asset_type
        is displayed

        :param project:       Name of the project
        :param asset_type:    Name of the sequence or asset type
        :param asset_name:    Name of the shot or asset
        :param fields:      Optional Shotgun fields to display
        :returns:           A dictionary with information on a shot or asset
        """
        if not fields: fields = []
        sg_project = self.get_sg_project(project)
        if self.get_sg_type(asset_type) == "Shot":
            sg_sequence = self.get_sg_sequence(sg_project, asset_type)
            return self.get_sg_shot(sg_project, sg_sequence, asset_name, fields)
        else:
            sg_asset_type = self.get_sg_asset_type(asset_type)       
            return self.get_sg_asset(sg_project, sg_asset_type, asset_name, fields)

    def read_type(self, project, asset_type, fields=None):
        """ Get values of Shotgun fields of either all shots in a given sequence
        or all assets in a given asset group. By default, information on id,
        code, type, and either sg_sequence or sg_asset_type is displayed

        :param project:     Name of the project
        :param asset_type:  Name of the sequence or asset type
        :param fields:      Optional Shotgun fields to display
        :returns:           A dictionary with information on shots or assets
        """
        if not fields: fields = []
        sg_project = self.get_sg_project(project)
        sg_type = self.get_sg_type(asset_type)
        sg_asset_type = self.get_sg_asset_type(asset_type)
        return self.get_sg_project_content(sg_type, sg_project, fields, sg_asset_type)

    def read_project_assets(self, project, fields=None):
        """ Get values of Shotgun fields of all assets in a given project.
        By default, information on id, code, type, and sg_asset_type is displayed

        :param project:     Name of the project
        :param fields:      Optional Shotgun fields to display
        :returns:           A dictionary with information on assets
        """
        if not fields: fields = []
        sg_project = self.get_sg_project(project)
        return self.get_sg_project_content("Asset", sg_project, fields)

    def read_project_shots(self, project, fields=None):
        """ Get values of Shotgun fields of all shots in a given project.
        By default, information on id, code, type, and sg_sequence is displayed

        :param project:     Name of the project
        :param fields:      Optional Shotgun fields to display
        :returns:           A dictionary with information on shots
        """
        if not fields: fields = []
        sg_project = self.get_sg_project(project)
        return self.get_sg_project_content("Shot", sg_project, fields)

    def __read_project(self, project, fields=None):
        """ Get values of Shotgun fields of all shots and assets in a given
        project. By default, information on id, code, type and either sg_sequence
        or sg_asset_type is displayed

        :param project:     Name of the project
        :param fields:      Optional Shotgun fields to display
        :returns:           A dictionary with information on shots
        """
        assets = self.read_project_assets(project, fields)
        shots = self.read_project_shots(project, fields)
        return assets + shots

    def get_assets_by_user(self, project, user, fields=None):
        """ Get values of Shotgun fields of all assets which have tasks
        assigned to a given user. By default, information on id, code, type,
        and sg_asset_type is displayed
        
        :param project:     Name of the project
        :param user:        First name and surname of a user (e.g. John Smith)
        :param fields:      Optional Shotgun fields to display
        :returns:           A dictionary with information on assets
        """
        if not fields: fields = []
        fields.append('tasks')
        sg_user = self.get_sg_user(user)
        sg_assets = self.read_project_assets(project, fields)
        result = list()
        for asset in sg_assets:
            for task in asset['tasks']:
                if self.check_task_user(task['id'], sg_user):
                    result.append(asset)
        return result

    def get_shots_by_user(self, project, user, fields=None):
        """ Get values of Shotgun fields of all shots which have tasks
        assigned to a given user. By default, information on id, code, type
        and sg_sequence is displayed

        :param project:     Name of the project
        :param user:        First name and surname of a user (e.g. John Smith)
        :param fields:      Optional Shotgun fields to display
        :returns:           A dictionary with information on shots
        """
        if not fields: fields = []
        fields.append('tasks')
        sg_user = self.get_sg_user(user)
        sg_shots = self.read_project_shots(project, fields)
        result = list()
        for shot in sg_shots:
            for task in shot['tasks']:
                if self.check_task_user(task['id'], sg_user):
                    result.append(shot)
        return result

    def __call__(self, cli_options):
        # Just bind options to self
        self.cli_options = cli_options


    def get_project_items(self, project, fields=None, sanitize=False):
        """ Reads project items from Shotgun. Shotgun unlike job-cli distingishes
            between shots and assets. We post-process these data to get what is more
            common for our side.  
        """
        from job.utils import AssetNameFilter as Filter
        result = []
        filter = Filter(not sanitize)
        items = self.__read_project(project)

        for item in items:
            assert "code" in item
            data = {'job_asset_name': filter(item['code'])}

            if item['type'] == 'Asset':
                data['job_asset_type'] = filter(item['sg_asset_type'])

            elif item['type'] == 'Shot':
                if not item['sg_sequence']:
                    continue
                data['job_asset_type'] = filter(item['sg_sequence']['name'])
            result += [data]
        return result


