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

STUDIO_SGTK_PATH = "/STUDIO/sgtk/studio/install/core/python"
#STUDIO_SGTK_PATH = "/home/ksalem/sgtk-test/studio/install/core/python/"


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

    def __read_entity_fields(self, entity_name):
        """ Get all fields used to describe a Shotgun entity
        
        :entity_name:           Entity name
        :returns:               List of Shotgun fields
        """
        schema = self.sg.schema_field_read(entity_name)
        fields = schema.keys()
        return sorted(fields)

    def __read_project(self, project, fields=None):
        """ Get a Shotgun Project entity
        
        :param project:         Project name
        :returns:               Project entity
        """
        filters = list()
        filters.append(["name", "is", project])
        if not fields: fields = []
        fields.extend(["name"])
        return self.sg.find_one("Project", filters, fields)

    def __read_asset_type(self, asset_type):
        """ Get a Shotgun AssetType entity

        :param asset_type:      AssetType name
        :returns:               AssetType entity
        """
        if asset_type == "char":
            return "Character"
        elif asset_type == "prop":
            return "Prop"
        elif asset_type == "set":
            return "Environment"
        else:
            return None

    def __read_sequence(self, sg_project, sequence, fields=None):
        """ Get a Shotgun Sequence entity
        
        :param sg_project:      Project entity
        :param sequence:        Sequence name
        :returns:               Sequence entity
        """
        filters = list()
        filters.append(["project", "is", sg_project])
        filters.append(["code", "is", sequence])
        if not fields: fields = []
        fields.extend(["code"])
        return self.sg.find_one("Sequence", filters, fields)

    def __read_asset(self, sg_project, sg_asset_type, asset_name, fields=None):
        """ Get a Shotgun Asset entity
        
        :param sg_project:      Project entity
        :param sg_asset_type:   AssetType entity
        :param asset_name:      Asset name
        :returns:               Asset entity
        """
        filters = list()
        filters.append(["project", "is", sg_project])
        filters.append(["sg_asset_type", "is", sg_asset_type])
        filters.append(["code", "is", asset_name])
        if not fields: fields = []
        fields.extend(["code", "sg_asset_type", "sg_sequence"])
        return self.sg.find_one("Asset", filters, fields)

    def __read_shot(self, sg_sequence, shot, fields=None):
        """ Get a Shotgun Shot entity
        
        :param sg_project:      Project entity
        :param sg_sequence:     Sequence entity
        :param shot:            Shot name
        :param fields:          Optional Shotgun fields
        :returns:               Shot entity
        """
        filters = list()
        filters.append(["sg_sequence", "is", sg_sequence])
        filters.append(["code", "is", shot])
        if not fields: fields = []
        fields.extend(["code", "sg_asset_type", "sg_sequence"])
        return self.sg.find_one("Shot", filters, fields)

    def __read_user(self, user, fields=None):
        """ Get a Shotgun HumanUser entity

        :param user:            User name
        :param fields:          Optional Shotgun fields
        :returns:               User entity
        """
        user = ".".join([user[:1], user[1:]])
        filters = list()
        filters.append(["login", "is", user])
        if not fields: fields = []
        fields.extend(["login"])
        return self.sg.find("HumanUser", filters, fields)

    def __read_project_items(self, sg_project, fields=None):
        """ Get all Shotgun Assset and Shot entities in a given project.
        By default, returned fields are: id, code, type, and either
        sg_asset_type or sg_sequence
        
        :param sg_project:      Project entity
        :param fields:          Optional Shotgun fields
        :returns:               List of Asset and Shot entities
        """
        sg_assets = self.__read_project_assets(sg_project, fields)
        sg_shots = self.__read_project_shots(sg_project, fields)
        return sg_assets + sg_shots

    def __read_project_assets(self, sg_project, fields=None):
        """ Get all Shotgun Asset entities in a given project.
        By default, returned fields are: type, id, code, and sg_asset_type

        :param sg_project:      Project entity
        :param fields:          Optional Shotgun fields
        :returns:               List of Asset entities
        """
        filters = list()
        filters.append(["project", "is", sg_project])
        if not fields: fields = []
        fields.extend(["code", "sg_asset_type"])
        return self.sg.find("Asset", filters, fields)

    def __read_project_assets_by_type(self, sg_project, sg_asset_type, fields=None):
        """ Get all Shotgun Asset entities of a selected type in a given project.
        By default, returned fields are: type, id, code, and sg_asset_type

        :param sg_project:      Project entity
        :param sg_asset_type:   AssetType entity
        :param fields:          Optional Shotgun fields
        :returns:               List of Asset entities
        """
        filters = list()
        filters.append(["project", "is", sg_project])
        filters.append(["sg_asset_type", "is", sg_asset_type])
        if not fields: fields = []
        fields.extend(["code", "sg_asset_type"])
        return self.sg.find("Asset", filters, fields)

    def __read_project_shots(self, sg_project, fields=None):
        """ Get all Shotgun Shot entities in a given project.
        By default, returned fields are: type, id, code, and sg_sequence

        :param sg_project:      Project entity
        :param fields:          Optional Shotgun fields
        :returns:               List of Shot entities
        """
        filters = list()
        filters.append(["project", "is", sg_project])
        if not fields: fields = []
        fields.extend(["code", "sg_sequence"])
        return self.sg.find("Shot", filters, fields)

    def __read_sequence_shots(self, sg_sequence, fields=None):
        """ Get all Shotgun Shot entities in a given sequence.
        By default, returned fields are: type, id, and code

        :param sg_project:      Project entity
        :param sg_sequence:     Sequence entity
        :param fields:          Optional Shotgun fields
        :returns:               List of Shot entities
        """
        filters = list()
        filters.append(["sg_sequence", "is", sg_sequence])
        if not fields: fields = []
        fields.extend(["code"])
        return self.sg.find("Shot", filters, fields)

    def __read_user_items(self, sg_project, sg_user, fields=None):
        """ Get all Shotgun Shot and Asset entities with tasks assigned to
        a given user
        
        :param sg_project:      Project entity
        :param sg_user:         User entity
        :param fields:          Optional Shotgun fields
        :returns:               List of Shot and Asset entities
        """
        sg_shots = self.__read_user_shots(sg_project, sg_user, fields)
        sg_assets = self.__read_user_assets(sg_project, sg_user, fields)
        return sg_shots + sg_assets

    def __read_user_tasks(self, sg_project, sg_user, fields=None):
        """ Get all Tasks assigned to a given user
        """
        filters = list()
        filters.append(["project", "is", sg_project])
        filters.append(["task_assignees", "is", sg_user])
        return self.sg.find("Task", filters)

    def __read_user_entities(self, sg_tasks, entity_name, fields=None):
        """ Get all entities with a tasks assigned to a selected user
        in a given project. By default, returned fields are: id, code, type.

        :param sg_tasks:        List of Task entities
        :param fields:          Optional Shotgun fields
        :returns:               List of Asset entities
        """
        # Create a list of tasks for a subfilter
        task_filter = list()
        for task in sg_tasks:
            task_filter.append(["tasks", "is", task])
        # Create a subfilter
        subfilter = dict()
        subfilter["filter_operator"] = "any"
        subfilter["filters"] = task_filter
        # Create new filters
        filters = list()
        filters.append(subfilter)
        # Make the final search
        if not fields: fields = []
        fields.extend(["code"])
        return self.sg.find(entity_name, filters, fields)

    def __read_user_assets(self, sg_tasks, fields=None):
        """ Get all Shotgun Asset entities with a tasks assigned to a selected
        user in a given project. By default, returned fields are: id, code, type.

        :param sg_tasks:        List of Task entities
        :param fields:          Optional Shotgun fields
        :returns:               List of Asset entities
        """
        return self.__read_user_entities(sg_tasks, "Asset", fields)

    def __read_user_shots(self, sg_tasks, fields=None):
        """ Get all Shotgun Shot entities with a tasks assigned to a selected
        user in a given user. By default, returned fields are: id, code, type.

        :param sg_tasks:        List of Task entities
        :param fields:          Optional Shotgun fields
        :returns:               List of Shot entities
        """
        return self.__read_user_entities(sg_tasks, "Shots", fields)

    def __create_project(self, project):
        """ Create a project in Shotgun
        
        :param project:         Project name
        :returns:               Project entity
        """
        data = {
            "name": project,
            "sg_status": "Active"
        }
        return self.sg.create("Project", data)

    def __create_sequence(self, sg_project, sequence):
        """ Create a sequence in Shotgun
        
        :param sg_project:      Project entity
        :param sequence:        Sequence name
        :returns:               Sequence entity
        """
        data = {
            "project": sg_project,
            "code": sequence
        }
        return self.sg.create("Sequence", data)

    def __create_asset(self, sg_project, sg_asset_type, asset_name):
        """ Create an asset in Shotgun
        
        :param sg_project:      Project entity
        :param sg_asset_type:   AssetType entity
        :param asset_name:      Asset name
        :returns                Asset entity
        """
        data = {
            "project": sg_project,
            "sg_asset_type": sg_asset_type,
            "code": asset_name
        }
        return self.sg.create("Asset", data)

    def __create_shot(self, sg_project, sg_sequence, shot):
        """ Create a shot in Shotgun
        
        :param sg_project:      Project entity
        :param sg_sequence:     Sequence entity
        :param shot:            Shot name
        :returns:               Shot entity
        """
        data = {
            "project": sg_project,
            "sg_sequence": sg_sequence,
            "code": shot
        }
        return self.sg.create("Shot", data)

    def __delete_project(self, sg_project):
        """ Remove a project from Shotgun
        
        :param sg_project:       Project entity
        :returns:               True or False
        """
        return self.sg.delete("Project", sg_project["id"])

    def __delete_sequence(self, sg_sequence):
        """ Remove a sequence form Shotgun
        
        :param sg_sequence:     Sequence entity
        :returns:               True or False
        """
        return self.sg.delete("Sequence", sg_sequence["id"])

    def __delete_asset(self, sg_asset):
        """ Remove an asset from Shotgun
        
        :param sg_asset         Asset entity
        :returns:               True or False
        """
        return self.sg.delete("Asset", sg_asset["id"])

    def __delete_shot(self, sg_shot):
        """ Remove a shot from Shotgun
        
        :param sg_shot:         Shot entity
        :returns:               True or False
        """
        return self.sg.delete("Shot", sg_shot["id"])

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
        items = self.__read_project_items(project)
        for item in items:
            assert "code" in item
            data = {"job_asset_name": filter(item["code"])}
            if item["type"] == "Asset":
                data["job_asset_type"] = filter(item["sg_asset_type"])
            elif item["type"] == "Shot":
                if not item["sg_sequence"]:
                    continue
                data["job_asset_type"] = filter(item["sg_sequence"]["name"])
            result += [data]
        return result

