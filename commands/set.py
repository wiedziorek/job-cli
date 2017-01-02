from .base import Base

import sys, os

# TODO: Find Rez and add its module to a path:
# rez_path = os.environ['REZ_CONFIG_FILE']
# rez_path = os.path.dirname(rez_path)
# rez_path = os.path.join()
sys.path.append("/opt/package/soft/rez/lib64/python2.7/site-packages/rez-2.0.rc1.28-py2.7.egg")


from rez.resolved_context import ResolvedContext
import subprocess


class SetJobEnvironment(Base):
    """ Sub command which performs setup of the environment per job.
    """
 
    def run(self):
        """ Entry point for sub command.
        """
        r = ResolvedContext(['houdini-15.5'])
        if not r.success:
            return 


        os.environ['JOB_CURRENT']    = self.options['PROJECT']
        os.environ['JOB_ASSET_TYPE'] = self.options['TYPE']
        os.environ['JOB_ASSET_NAME'] = self.options['ASSET']

        r.print_info()
        r.execute_shell()






      