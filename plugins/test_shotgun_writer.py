#!/usr/bin/python
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

# Test Shotgun Writer plugin
from job.plugin import PluginManager
import plugins
manager = PluginManager()
writer = manager.get_plugin_by_name("ShotgunWriter")


class TestShotgunWriter(unittest.TestCase):

    def test_create_asset(self):
        """ Test create_asset() method
        """
        command = writer.create_asset("test2", "char", "bar")
        print command

    def test_create_shot(self):
        """ Test create_shot() method
        """
        command = writer.create_shot("foo", "eggs", "egg0080")
        print command

    def test_create_sequence(self):
        """ Test create sequence() methd
        """
        command = writer.create_sequence("foo", "eggs2")
        print command

    def test_create_project(self):
        """ Test create_project() method
        """
        command = writer.create_project("spam")
        print command


if __name__ == '__main__':
    unittest.main()
