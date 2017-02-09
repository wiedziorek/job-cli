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

# Test Shotgun Reader plugin
from job.plugin import PluginManager
import plugins
manager = PluginManager()
reader = manager.get_plugin_by_name("ShotgunReader")


class TestShotgunReader(unittest.TestCase):

    def test_get_asset_fields(self):
        """ Test get_asset_fields() method
        """
        command = reader.get_asset_fields()
        result = \
        [
            'addressings_cc', 'asset_library_sg_ha_assets_asset_libraries',
            'assets', 'cached_display_name', 'code', 'created_at',
            'created_by', 'description', 'filmstrip_image', 'id', 'image',
            'mocap_takes', 'notes', 'open_notes','open_notes_count', 'parents',
            'project', 'sequences', 'sg_asset_type', 'sg_episodes',
            'sg_published_files', 'sg_status_list', 'sg_texture_stat',
            'sg_versions', 'shoot_days', 'shots', 'step_0', 'step_10',
            'step_11', 'step_12', 'step_14', 'step_15', 'step_16', 'step_17',
            'step_18', 'step_19', 'step_20', 'step_30', 'step_9', 'tag_list',
            'task_template', 'tasks', 'updated_at', 'updated_by'
        ]
        self.assertEqual(command, result)

    def test_get_shot_fields(self):
        """ Test get_shot_fields() method
        """
        command = reader.get_shot_fields()
        result = \
        [
            'addressings_cc', 'assets', 'cached_display_name', 'code',
            'created_at', 'created_by', 'cut_duration', 'cut_in', 'cut_out',
            'description', 'filmstrip_image', 'head_duration', 'head_in',
            'head_out', 'id', 'image', 'notes', 'open_notes',
            'open_notes_count', 'parent_shots', 'project', 'sg_animatortmp',
            'sg_box_scale', 'sg_camera_type', 'sg_cut_duration', 'sg_cut_in',
            'sg_cut_order', 'sg_cut_out', 'sg_end_date', 'sg_episodes',
            'sg_format', 'sg_ha_blocking_status', 'sg_ha_cameras',
            'sg_ha_sataus', 'sg_ha_sort', 'sg_head_in', 'sg_lens',
            'sg_old_cut_duration', 'sg_orginal_resolution',
            'sg_published_files', 'sg_sequence', 'sg_shot_type',
            'sg_skala_berlinek', 'sg_skala_berlinek_bk',
            'sg_skala_berlinek_lod', 'sg_start_date', 'sg_status_list',
            'sg_tail_out', 'sg_versions', 'sg_working_duration', 'shots',
            'smart_cut_duration', 'smart_cut_in', 'smart_cut_out',
            'smart_cut_summary_display', 'smart_duration_summary_display',
            'smart_head_duration', 'smart_head_in', 'smart_head_out',
            'smart_tail_duration', 'smart_tail_in', 'smart_tail_out',
            'smart_working_duration', 'step_0', 'step_13', 'step_21', 'step_25',
            'step_26', 'step_28', 'step_29', 'step_32', 'step_5', 'step_6',
            'step_7', 'step_8', 'tag_list', 'tail_duration', 'tail_in',
            'tail_out', 'task_template', 'tasks', 'updated_at', 'updated_by'
        ]
        self.assertEqual(command, result)

    def test_read_asset_char(self):
        """ Test read_asset() method. Query about a character asset
        """
        command = reader.read_asset('test', 'char', 'boy')
        result = \
        [
            {
                'type': 'Asset',
                'id': 2118,
                'code': 'boy',
                'sg_asset_type': 'Character'
            }
        ]
        self.assertEqual(command, result)


    def test_read_asset_char_fields(self):
        """ Test read_asset() method. Query about a character asset.
        Give extra fields to display
        """
        command = reader.read_asset('test', 'char', 'boy', ['sg_status_list'])
        result = \
        [
            {
                'type': 'Asset',
                'id': 2118,
                'code': 'boy',
                'sg_asset_type': 'Character',
                'sg_status_list': 'wtg'
            },
        ]
        self.assertEqual(command, result)
    
    def test_read_asset_shot(self):
        """ Test read_asset() method. Query about a shot
        """
        command = reader.read_asset('test', 'foo', 'foo0010')
        result = \
        [
            {
                'type': 'Shot',
                'id': 3426,
                'code': 'foo0010',
                'sg_sequence':
                {
                    'type': 'Sequence',
                    'id': 203,
                    'name': 'foo'
                },
            }
        ]
        self.assertEqual(command, result)

    def test_read_asset_shot_fields(self):
        """ Test read_asset() method. Query about a shot.
        Give extra fields to display
        """
        command = reader.read_asset('test', 'foo', 'foo0010', ['sg_status_list'])
        result = \
        [
            {
                'type': 'Shot',
                'id': 3426,
                'code': 'foo0010',
                'sg_sequence':
                {
                    'type': 'Sequence',
                    'id': 203,
                    'name': 'foo'
                },
                'sg_status_list': 'wtg'
            }
        ]
        self.assertEqual(command, result)

    def test_read_type_sequence(self):
        """ Test read_type() method. Query about a sequence
        """
        command = reader.read_type('test', 'foo')
        result = \
        [
            {
                'type': 'Shot',
                'id': 3426,
                'code': 'foo0010',
                'sg_sequence':
                {
                    'type': 'Sequence',
                    'id': 203,
                    'name': 'foo'
                }
            }
        ]
        self.assertEqual(command, result)

    def test_read_type_sequence_fields(self):
        """ Test read_type() method. Query about a sequence.
        Give extra fields to display
        """
        command = reader.read_type('test', 'foo', ['sg_status_list'])
        result = \
        [
            {
                'type': 'Shot',
                'id': 3426,
                'code': 'foo0010',
                'sg_sequence':
                {
                    'type': 'Sequence',
                    'id': 203,
                    'name': 'foo'
                },
                'sg_status_list': 'wtg'
            }
        ]
        self.assertEqual(command, result)

    def test_read_type_char(self):
        """ Test read_type() method. Query about an asset group
        """
        command = reader.read_type('test', 'char')
        result = \
        [
            {
                'type': 'Asset',
                'id': 2118,
                'code': 'boy',
                'sg_asset_type': 'Character'
            }
        ]
        self.assertEqual(command, result)

    def test_read_type_char_fields(self):
        """ Test read_type() method. Query about an asset group.
        Give extra fields to display
        """
        command = reader.read_type('test', 'char', ['sg_status_list'])
        result = \
        [
            {
                'type': 'Asset',
                'id': 2118,
                'code': 'boy',
                'sg_asset_type': 'Character',
                'sg_status_list': 'wtg'
            }
        ]
        self.assertEqual(command, result)

    def test_read_project_assets(self):
        """ Test read_project_assets() method
        """
        command = reader.read_project_assets('test')
        result = \
        [
            {
                'type': 'Asset',
                'id': 2118,
                'code': 'boy',
                'sg_asset_type': 'Character'
            }
        ]
        self.assertEqual(command, result)

    def test_read_project_assets_fields(self):
        """ Test read_project_assets() method. Give extra fields to display
        """
        command = reader.read_project_assets('test', ['sg_status_list'])
        result = \
        [
            {
                'type': 'Asset',
                'id': 2118,
                'code': 'boy',
                'sg_asset_type': 'Character',
                'sg_status_list': 'wtg'
            }
        ]
        self.assertEqual(command, result)

    def test_read_project_shots(self):
        """ Test read_project_shots() method
        """
        command = reader.read_project_shots('test')
        result = \
        [
            {
                'type': 'Shot',
                'id': 3426,
                'code': 'foo0010',
                'sg_sequence':
                {
                    'type': 'Sequence',
                    'id': 203,
                    'name': 'foo'
                }
            }
        ]
        self.assertEqual(command, result)

    def test_read_project_shots_fields(self):
        """ Test read_project_shots() method. Give extra fields to display
        """
        command = reader.read_project_shots('test', ['sg_status_list'])
        result = \
        [
            {
                'type': 'Shot',
                'id': 3426,
                'code': 'foo0010',
                'sg_sequence':
                {
                    'type': 'Sequence',
                    'id': 203,
                    'name': 'foo'
                },
                'sg_status_list': 'wtg'
            }
        ]
        self.assertEqual(command, result)

    def test_read_project(self):
        """ Test read_project() method
        """
        command = reader.read_project('test')
        result = \
        [
            {
                'type': 'Asset',
                'id': 2118,
                'code': 'boy',
                'sg_asset_type': 'Character'
            },
            {
                'type': 'Shot',
                'id': 3426,
                'code': 'foo0010',
                'sg_sequence':
                {
                    'type': 'Sequence',
                    'id': 203,
                    'name': 'foo'
                }
            }
        ]
        self.assertEqual(command, result)

    def test_read_project_fields(self):
        """ Test read_project() method. Give extra fields to display
        """
        command = reader.read_project('test', ['sg_status_list'])
        result = \
        [
            {
                'type': 'Asset',
                'id': 2118,
                'code': 'boy',
                'sg_asset_type': 'Character',
                'sg_status_list': 'wtg'
            },
            {
                'type': 'Shot',
                'id': 3426,
                'code': 'foo0010',
                'sg_sequence':
                {
                    'type': 'Sequence',
                    'id': 203,
                    'name': 'foo'
                },
                'sg_status_list': 'wtg'
            }
        ]
        self.assertEqual(command, result)

    def test_get_shots_by_user(self):
        """ Test get_shots_by_user() method
        """
        command = reader.get_shots_by_user('test', 'Kamil Salem')
        result = \
        [
            {
                'type': 'Shot',
                'id': 3426,
                'code': 'foo0010',
                'sg_sequence':
                {
                    'type': 'Sequence',
                    'id': 203,
                    'name': 'foo',
                },
                'tasks':
                [
                    {
                        'type': 'Task',
                        'id': 24480,
                        'name': 'body_animation'
                    }
                ]
            }
        ]
        self.assertEqual(command, result)
 
    def test_get_shots_by_user_fields(self):
        """ Test get_shots_by_user() method. Give extra fields to display
        """
        command = reader.get_shots_by_user('test', 'Kamil Salem',
                                            ['sg_status_list'])
        result = \
        [
            {
                'type': 'Shot',
                'id': 3426,
                'code': 'foo0010',
                'sg_sequence':
                {
                    'type': 'Sequence',
                    'id': 203,
                    'name': 'foo'
                },
                'sg_status_list': 'wtg',
                'tasks':
                [
                    {
                        'type': 'Task',
                        'id': 24480,
                        'name': 'body_animation'
                    }
                ]
            }
        ]
        self.assertEqual(command, result)

    def test_get_assets_by_user(self):
        """ Test get_assets_by_user() method
        """
        command = reader.get_assets_by_user('test', 'Kamil Salem')
        result = \
        [
            {
                'type': 'Asset',
                'id': 2118,
                'code': 'boy',
                'sg_asset_type': 'Character',
                'tasks':
                [
                    {
                        'type': 'Task',
                        'id': 24479,
                        'name': 'body_rig'
                    }
                ]
            }
        ]
        self.assertEqual(command, result)

    def test_get_assets_by_user_fields(self):
        """ Test get_assets_by_user() method. Give extra fields to display
        """
        command = reader.get_assets_by_user('test', 'Kamil Salem',
                                            ['sg_status_list'])
        result = \
        [
            {
                'type': 'Asset',
                'id': 2118,
                'code': 'boy',
                'sg_asset_type': 'Character',
                'sg_status_list': 'wtg',
                'tasks':
                [
                    {
                        'type': 'Task',
                        'id': 24479,
                        'name': 'body_rig'
                    }
                ]
            }
        ]
        self.assertEqual(command, result)

if __name__ == '__main__':
    unittest.main()
