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
from rez.package_maker__ import PackageMaker
from rez.packages_ import create_package, get_package
from rez import config
import subprocess


class SetJobEnvironment(Base):
    """ Sub command which performs setup of the environment per job.
    """
 
    def run(self):
        """ Entry point for sub command.
        """
        from tempfile import mkdtemp
        temp_shot_package = mkdtemp()
        rez_config = config.create_config()

        job_name  = self.options['PROJECT']
        job_group = self.options['TYPE']
        job_asset = self.options['ASSET']

        version = "%s-%s" % (job_group, job_asset)

        commands   = ['export JOB_CURRENT=%s' % job_name]
        commands  += ['export JOB_ASSET_TYPE=%s' % job_group]
        commands  += ['export JOB_ASSET_NAME=%s' % job_asset]

        data = {'version': version, 'name': job_name, 
                'uuid'   : 'repository.%s' % job_name,
                'variants':[],
                'commands': commands}

        package = create_package(job_name, data)
        variant = package.get_variant()
        variant.install(temp_shot_package)
        import time
  
        rez_name = "%s-%s-%s" % (job_name, job_group, job_asset)
        package_paths = [temp_shot_package] + rez_config.packages_path

        r = ResolvedContext([rez_name, 'houdini'], package_paths=package_paths)

        if not r.success:
            print r
            return 

        r.print_info()
        r.execute_shell()






      