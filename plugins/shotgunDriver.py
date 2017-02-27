# -*- coding: utf-8 -*-

##########################################################################
#
#  Copyright (c) 2017, Human Ark Animation Studio. All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#
#     * Neither the name of Human Ark Animation Studio nor the names of any
#       other contributors to this software may be used to endorse or
#       promote products derived from this software without specific prior
#       written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
#  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
#  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
#  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
#  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
##########################################################################

# Import Job modules
from job.plugin import PluginManager, PluginType, DatabaseDriver

#STUDIO_SGTK_PATH = "/STUDIO/sgtk/studio/install/core/python"
STUDIO_SGTK_PATH = "/home/ksalem/sgtk-test/studio/install/core/python/"


class ShotgunDriver(DatabaseDriver, PluginManager):
    name = "ShotgunDriver"
    logger = None
    # Type specified in DatabaseDriver as OptionReader

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
        # Create connection.
        self.sg = sgtk.util.shotgun.create_sg_connection()
        if self.sg:
            self.logger.debug("%s registering as %s", self.name, self.type)
            return True

    def get_sg_type(self, ha_type):
        if ha_type in ["char", "prop", "set"]:
            return "Asset"
        else:
            return "Shot"

    def get_sg_asset_type(self, ha_type):
        if ha_type == "char":
            return "Character"
        elif ha_type == "prop":
            return "Prop"
        elif ha_type == "set":
            return "Environment"
        else:
            return None

    def get_sg_project(self, name):
        return self.sg.find_one("Project", [["name", "is", name]])

    def get_sg_sequence(self, project, code):
        filters = list()
        filters.append(["project", "is", project])
        filters.append(["code", "is", code])
        return self.sg.find_one("Sequence", filters)

    def get_sg_asset(self, sg_project, sg_asset_type, code, fields=None):
        if not fields: fields = []
        filters = list()
        filters.append(["project", "is", sg_project])
        filters.append(["sg_asset_type", "is", sg_asset_type])
        filters.append(["code", "is", code])
        fields.extend(["code", "sg_asset_type", "sg_sequence"])
        return self.sg.find("Asset", filters, fields)

    def get_sg_shot(self, sg_project, sg_sequence, code, fields=None):
        if not fields: fields = []
        filters = list()
        filters.append(["project", "is", sg_project])
        filters.append(["sg_sequence", "is", sg_sequence])
        filters.append(["code", "is", code])
        fields.extend(["code", "sg_asset_type", "sg_sequence"])
        return self.sg.find("Shot", filters, fields)

    def get_sg_project_content(self, sg_type, sg_project, fields=None,
                                     sg_asset_type=None):
        if not fields: fields = []
        filters = list()
        filters.append(["project", "is", sg_project])
        if sg_asset_type:
            filters.append(["sg_asset_type", "is", sg_asset_type])
        fields.extend(["code", "sg_asset_type", "sg_sequence"])
        return self.sg.find(sg_type, filters, fields)

    def get_asset_tasks(self, sg_assets, sg_user):
        filters = list()
        filters.append(["asset", "in", sg_assets])
        filters.append(["task_assignees", "contains", sg_user])
        return self.sg.find("Task", filters)

    def get_sg_user(self, name):
        filters = list()
        filters.append(["name", "is", name])
        return self.sg.find("HumanUser", filters)

    def check_task_user(self, task_id, sg_user):
        filters = list()
        filters.append(["id", "is", task_id])
        filters.append(["task_assignees", "is", sg_user])
        return self.sg.find_one("Task", filters)

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

    def create_asset(self, project, asset_type, asset_name):
        """ Create an asset in Shotgun
        :param project:     Name of the project
        :param asset_type:  Name of the asset type
        :param asset_name:  Name of the asset
        :returns:           A dictionary with the information on the new asset
        """
        sg_project = self.get_sg_project(project)
        if not sg_project:
            sg_project = self.create_project(project)
        sg_asset_type = self.get_sg_asset_type(asset_type)
        if self.get_sg_asset(sg_project, sg_asset_type, asset_name):
            raise ValueError ("Asset already exists!")
        data = {
            "project": sg_project,
            "sg_asset_type": sg_asset_type,
            "code": asset_name
        }
        return self.sg.create("Asset", data)
        return data

    def create_shot(self, project, sequence, shot):
        """ Create a shot in Shotgun
        :param project:     Name of the project
        :param sequence:    Name of the sequence
        :param shot:        Name of the shot
        :returns:           A dictionary with the information on the new shot
        """
        sg_project = self.get_sg_project(project)
        if not sg_project:
            sg_project = self.create_project(project)
        sg_sequence = self.get_sg_sequence(sg_project, sequence)
        if not sg_sequence:
            sg_sequence = self.create_sequence(sg_project, sequence)
        if self.get_sg_shot(sg_project, sg_sequence, shot):
            raise ValueError ("Shot already exists!")
        data = {
            "project": sg_project,
            "sg_sequence": sg_sequence,
            "code": shot
        }
        return self.sg.create("Shot", data)
        return data

    def create_sequence(self, project, sequence):
        """ Create a sequence in Shotgun
        :param project:     Name of the project
        :param sequence:    Name of the sequence
        :returns:           A dictionary with the information on the new
                            sequence
        """
        sg_project = self.get_sg_project(project)
        if not sg_project:
            sg_project = self.create_project(project)
        sg_sequence = self.get_sg_sequence(sg_project, sequence)
        if sg_sequence:
            raise ValueError ("Sequence already exists!")
        data = {
            "project": sg_project,
            "code": sequence
        }
        return self.sg.create("Sequence", data)
        return data

    def create_project(self, project):
        """ Create a project in Shotgun
        :param project:     Name of the project
        :returns:           A dictionary with the information on the new
                            project
        """
        sg_project = self.get_sg_project(project)
        if sg_project:
            raise ValueError ("Project already exists!")
        data = {
            "name": project,
            "sg_status": "Active"
        }
        return self.sg.create("Project", data)

    def __delete_project(self):
        pass

    def __delete_sequence(self):
        pass

    def __delete_shot(self):
        pass

    def __delete_asset(self):
        pass

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
