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




class JobEnvironment(object):
    options  = None
    job_path = None
    def __init__(self, log_level='INFO', options=None):
        from job.cli import JobTemplate
        self.options = options
        self.job_name  = self.options['PROJECT']
        self.job_group = self.options['TYPE']
        self.job_asset = self.options['ASSET']
        self.log_level = log_level
        if self.options['--root']:
            root = self.options['--root']
        else:
            root = None

          # Pack arguments so we can ommit None one (like root):
        kwargs = {}
        kwargs['job_name']  = self.job_name
        kwargs['job_group'] = self.job_group
        kwargs['log_level'] = self.log_level
        if root:
            kwargs['root']  = rot

        job = JobTemplate(**kwargs)
        if not self.options['--no_local_schema']:
            local_schema_path = job.get_local_schema_path()
            job.load_schemas(local_schema_path)
            super(JobTemplate, job).__init__(job.schema, "job", **kwargs)

        job_path = job.expand_path_template()
        self.job_path = job_path

    def create_exports(self, name_values):
        exports = []
        for n, v in name_values:
            exports += ['export %s=%s' % (n, v)]
        return exports



class JobRezEnvironment(JobEnvironment):
    def __init__(self, log_level='INFO', options=None):
        super(JobRezEnvironment, self).__init__(log_level=log_level, options=options)
        self.options = options
        self.data    = {}
        from rez import config
        self.rez_config = config.create_config()
        self.rez_name  = "%s-%s-%s" % (self.job_name, 
                                       self.job_group, 
                                       self.job_asset)

        self.rez_version = "%s-%s" % (self.job_group, self.job_asset)

        commands = self.create_exports((('JOB_CURRENT',    self.job_name), 
                                        ('JOB_ASSET_TYPE', self.job_group),
                                        ('JOB_ASSET_NAME', self.job_asset),
                                        ('JOB', self.job_path)))


        data = {'version': self.rez_version, 'name': self.job_name, 
                'uuid'   : 'repository.%s' % self.job_name,
                'variants':[],
                'commands': commands}

        self.data = data

    def __call__(self, path):
        """
        """
        if self.create_rez_package(self.data):
            self.install_rez_package(path)
            return True
        return False

    def create_rez_package(self, data):
        """
        """
        from rez.packages_ import create_package
        self.package = create_package(data['name'], data)
        return self.package

    def install_rez_package(self, path):
        """
        """
        variant = self.package.get_variant()
        variant.install(path)
        

class SetJobEnvironment(Base):
    """ Sub command which performs setup of the environment per job.
    """
 
    def run(self):
        """ Entry point for sub command.
        """
        from tempfile import mkdtemp
        from rez.resolved_context import ResolvedContext

        temp_job_package_path = mkdtemp()
        log_level = self.get_log_level_from_options(self.options)
        context   = JobRezEnvironment(log_level, self.options)

        if not context(path=temp_job_package_path):
            print "Somehting went wrong. can't set."
            raise OSError

        package_paths = [temp_job_package_path] + context.rez_config.packages_path
        r = ResolvedContext([context.rez_name, 'houdini'], package_paths=package_paths)

        if not r.success:
            return 

        r.print_info()
        r.execute_shell()






      