from .base import Base

import sys, os
from glob import glob

# TODO: Find Rez and add its module to a path (elegantly)
if not os.getenv("REZ_CONFIG_FILE", None):
    try:
        import rez
    except ImportError, e:
        print "Can't find rez.", e
        raise ImportError
else:
    rez_path = os.environ['REZ_CONFIG_FILE']
    rez_path = os.path.dirname(rez_path)
    rez_candidate = os.path.join(rez_path, "lib64/python2.7/site-packages/rez-*.egg")
    rez_candidate = glob(rez_candidate)
    if rez_candidate:
        sys.path.append(rez_candidate[0])
    else:
        print "Can't find rez."
        raise ImportError


from rez.resolved_context import ResolvedContext
import subprocess


class SetJobEnvironment(Base):
    """ Sub command which performs setup of the environment per job.
    """
 
    def run(self):
        """ Entry point for sub command.
        """
        r = ResolvedContext(['houdini'])
        if not r.success:
            return 


        os.environ['JOB_CURRENT']    = self.options['PROJECT']
        os.environ['JOB_ASSET_TYPE'] = self.options['TYPE']
        os.environ['JOB_ASSET_NAME'] = self.options['ASSET']

        r.print_info()
        r.execute_shell()






      