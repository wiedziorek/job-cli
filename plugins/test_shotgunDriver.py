import sys
from os.path import realpath, dirname, join
import unittest

# Get root directory
job_root_path = dirname(realpath(__file__))
job_root_path = dirname(job_root_path)
local_schematics_path = join(job_root_path, "schematics")
sys.path.append(job_root_path)
sys.path.append(local_schematics_path)

# Make sure we can import main module
try:
    from job.plugin import PluginManager
    import plugins
except ImportError, error:
    print error
    raise

# Test Shotgun Driver plugin
from job.plugin import PluginManager
import plugins
manager = PluginManager()
driver = manager.get_plugin_by_name("ShotgunDriver")

# Import modules needed for testing
import os
import json
import time


class TestShotgunDriver(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestShotgunDriver, self).__init__(*args, **kwargs)
        self.results = self.load_results()
        
    def load_results(self):
        dir_path = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(dir_path, "test_shotgunDriver.json")
        with open(file_path, "r") as file_:
            contents = json.load(file_)
        return contents

    def test_read_entity_fields(self):
        """ Get all fields used to descibe a Shotgun Asset entity
        """
        command = driver._ShotgunDriver__read_entity_fields("Asset")
        result = self.assertEqual(command, self.results["read_entity_fields"])

    def test_read_project(self):
        """ Get a Shotgun Project entity
        """
        command = driver._ShotgunDriver__read_project("BIG BUCK BUNNY")
        result = self.assertEqual(command, self.results["read_project"])

    def test_read_project_fields(self):
        """ Get a Shotgun Project entity with optional fields
        """
        fields = ["sg_status"]
        command = driver._ShotgunDriver__read_project("BIG BUCK BUNNY", fields)
        self.assertEqual(command, self.results["read_project_fields"])

    def test_read_asset_type(self):
        """ Get a Shotgun AssetType entity
        """
        command = driver._ShotgunDriver__read_asset_type("char")
        self.assertEqual(command, "Character")

    def test_read_sequence(self):
        """ Get a Shotgun Sequence entity
        """
        sg_project = driver._ShotgunDriver__read_project("BIG BUCK BUNNY")
        command = driver._ShotgunDriver__read_sequence(sg_project, "bunny_010")
        self.assertEqual(command, self.results["read_sequence"])

    def test_read_sequence_fields(self):
        """ Get a Shotgun Sequence entity with optional fields
        """
        sg_project = driver._ShotgunDriver__read_project("BIG BUCK BUNNY")
        fields = ["description"]
        command = driver._ShotgunDriver__read_sequence(sg_project, "bunny_010", fields)
        self.assertEqual(command, self.results["read_sequence_fields"])

    def test_read_asset(self):
        """ Get a Shotgun Asset entity
        """
        sg_project = driver._ShotgunDriver__read_project("BIG BUCK BUNNY")
        sg_asset_type = driver._ShotgunDriver__read_asset_type("char")
        command = driver._ShotgunDriver__read_asset(sg_project, sg_asset_type, "Bunny")
        self.assertEqual(command, self.results["read_asset"])

    def test_read_asset_fields(self):
        """ Get a Shotgun Asset entity with optional fields
        """
        sg_project = driver._ShotgunDriver__read_project("BIG BUCK BUNNY")
        sg_asset_type = driver._ShotgunDriver__read_asset_type("char")
        fields = ["description"]
        command = driver._ShotgunDriver__read_asset(sg_project, sg_asset_type, "Bunny", fields)
        self.assertEqual(command, self.results["read_asset_fields"])

    def test_read_shot(self):
        """ Get a Shotgun Shot entity
        """
        sg_project = driver._ShotgunDriver__read_project("BIG BUCK BUNNY")
        sg_sequence = driver._ShotgunDriver__read_sequence(sg_project, "bunny_010")
        command = driver._ShotgunDriver__read_shot(sg_sequence, "bunny_010_0010")
        self.assertEqual(command, self.results["read_shot"])

    def test_read_shot_fields(self):
        """ Get a Shotgun Shot entity with optional fields
        """
        sg_project = driver._ShotgunDriver__read_project("BIG BUCK BUNNY")
        sg_sequence = driver._ShotgunDriver__read_sequence(sg_project, "bunny_010")
        fields = ["description"]
        command = driver._ShotgunDriver__read_shot(sg_sequence, "bunny_010_0010", fields)
        self.assertEqual(command, self.results["read_shot_fields"])

    def test_read_user(self):
        """ Get a Shotgun User entity
        """
        command = driver._ShotgunDriver__read_user("ksalem")
        self.assertEqual(command, self.results["read_user"])

    def test_read_user_fields(self):
        """ Get a Shotgun User entity with optional fields
        """
        fields = ["department"]
        command = driver._ShotgunDriver__read_user("ksalem", fields)
        self.assertEqual(command, self.results["read_user_fields"])

    def test_read_project_items(self):
        """ Get all Shotgun Asset and Shot entities in a given project
        """
        sg_project = driver._ShotgunDriver__read_project("BIG BUCK BUNNY")
        command = driver._ShotgunDriver__read_project_items(sg_project)
        self.assertEqual(command, self.results["read_project_items"])

    def test_read_project_assets(self):
        """ Get all Shotgun Asset entities in a given project
        """
        sg_project = driver._ShotgunDriver__read_project("BIG BUCK BUNNY")
        command = driver._ShotgunDriver__read_project_assets(sg_project)
        self.assertEqual(command, self.results["read_project_assets"])

    def test_read_project_assets_by_type(self):
        """ Get all Shotgun Asset entities of a selected type in a given project
        """
        sg_project = driver._ShotgunDriver__read_project("BIG BUCK BUNNY")
        sg_asset_type = driver._ShotgunDriver__read_asset_type("char")
        command = driver._ShotgunDriver__read_project_assets_by_type(sg_project, sg_asset_type)
        self.assertEqual(command, self.results["read_project_assets_by_type"])

    def test_read_project_shots(self):
        """ Get all Shotgun Asset entities in a given project
        """
        sg_project = driver._ShotgunDriver__read_project("BIG BUCK BUNNY")
        command = driver._ShotgunDriver__read_project_shots(sg_project)
        self.assertEqual(command, self.results["read_project_shots"])

    def test_read_sequence_shots(self):
        """ Get all Shotgun Shot entities in a given sequence
        """
        sg_project = driver._ShotgunDriver__read_project("BIG BUCK BUNNY")
        sg_sequence = driver._ShotgunDriver__read_sequence(sg_project, "bunny_010")
        command = driver._ShotgunDriver__read_sequence_shots(sg_sequence)
        self.assertEqual(command, self.results["read_sequence_shots"])

    def test_read_user_assets(self):
        """ Get all Shotgun Assets entities with task assigned to a given user
        """
        sg_project = driver._ShotgunDriver__read_project("BIG BUCK BUNNY")
        sg_user = driver._ShotgunDriver__read_user("ksalem")
        sg_tasks = driver._ShotgunDriver__read_user_tasks(sg_project, sg_user)
        command = driver._ShotgunDriver__read_user_assets(sg_tasks)
        self.assertEqual(command, self.results["read_user_assets"])
    
    def test_create_delete_project(self):
        """ Create a project in Shotgun than delete it
        """
        date = str(int(time.time()))
        name = "_".join(["test", date])
        sg_project = driver._ShotgunDriver__create_project(name)
        command = driver._ShotgunDriver__delete_project(sg_project)
        self.assertEqual(command, True)

    def test_create_delete_sequence(self):
        """ Create a sequence in Shotgun than delete it
        """
        date = str(int(time.time()))
        name = "_".join(["test", date])
        sg_project = driver._ShotgunDriver__read_project("sgtkTest")
        sg_sequence = driver._ShotgunDriver__create_sequence(sg_project, name)
        command = driver._ShotgunDriver__delete_sequence(sg_sequence)
        self.assertEqual(command, True)

    def test_create_delete_asset(self):
        """ Create an asset in Shotgun than delete it
        """
        date = str(int(time.time()))
        name = "_".join(["test", date])
        sg_project = driver._ShotgunDriver__read_project("sgtkTest")
        sg_asset_type = driver._ShotgunDriver__read_asset_type("prop")
        sg_asset = driver._ShotgunDriver__create_asset(sg_project, sg_asset_type, name)
        command = driver._ShotgunDriver__delete_asset(sg_asset)
        self.assertEqual(command, True)

    def test_create_delete_shot(self):
        """ Create a shot in Shotgun than delete it
        """
        date = str(int(time.time()))
        name = "_".join(["test", date])
        sg_project = driver._ShotgunDriver__read_project("sgtkTest")
        sg_sequence = driver._ShotgunDriver__read_sequence(sg_project, "sgtkTest")
        sg_shot = driver._ShotgunDriver__create_shot(sg_project, sg_sequence, name)
        command = driver._ShotgunDriver__delete_shot(sg_shot)
        self.assertEqual(command, True)


if __name__ == "__main__":
    unittest.main()
