from .base import BaseSubCommand

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
    cli_options  = None
    job_path = None
    def __init__(self, cli_options, log_level='INFO'):
        from job.cli import JobTemplate
        self.cli_options = cli_options
        self.job_name  = self.cli_options['PROJECT']
        self.job_group = self.cli_options['TYPE']
        self.job_asset = self.cli_options['ASSET']
        self.log_level = log_level
        if self.cli_options['--root']:
            root = self.cli_options['--root']
        else:
            root = None

        # Pack arguments so we can ommit None one (like root):
        kwargs = {}
        kwargs['job_name']  = self.job_name
        kwargs['job_group'] = self.job_group
        kwargs['log_level'] = self.log_level
        if root:
            kwargs['root']  = root

        self.job_template = JobTemplate(**kwargs)
        if not self.cli_options['--no-local-schema']:
            local_schema_path = self.job_template.get_local_schema_path()
            self.job_template.load_schemas(local_schema_path)
            super(JobTemplate, self.job_template).__init__(self.job_template.schema, "job", **kwargs)

        job_path = self.job_template.expand_path_template()
        self.job_path = job_path

    def create_exports(self, name_values):
        exports = []
        for n, v in name_values:
            exports += ['export %s=%s' % (n, v)]
        return exports



class JobRezEnvironment(JobEnvironment):
    def __init__(self, cli_options, log_level='INFO'):
        super(JobRezEnvironment, self).__init__(cli_options, log_level=log_level)
        self.cli_options = cli_options
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


class SetJobEnvironment(BaseSubCommand):
    """ Sub command which performs setup of the environment per job.
    """
 
    def run(self):
        """ Entry point for sub command.
        """
        from tempfile import mkdtemp
        from rez.resolved_context import ResolvedContext
        from rez.packages_ import get_latest_package
        from job.utils import setup_logger, get_log_level_from_options

        log_level = get_log_level_from_options(self.cli_options)
        self.logger = setup_logger("Plugin", log_level=log_level)

        user_job_package_path = os.path.join(os.getenv("HOME"), ".job")
        if not os.path.isdir(user_job_package_path):
            os.mkdir(user_job_package_path)

        rez_context_maker = JobRezEnvironment(self.cli_options, log_level=log_level)
        package_paths     = [user_job_package_path] + rez_context_maker.rez_config.packages_path


        # Reading options from command line and saved in job.opt(s)
        # How to make it cleaner?
        rez_package_names = []
        # Job option pass:
        if "--rez" in rez_context_maker.job_template.job_options:
            rez_package_names += rez_context_maker.job_template.job_options['--rez']
        # Command line pass:
        if self.cli_options['--rez']:
            rez_package_names += self.cli_options['--rez']
        rez_package_names += [rez_context_maker.rez_name]

        # Lets try if packages was already created:
        if not get_latest_package(rez_context_maker.data['name'], \
            range_=rez_context_maker.data['version'], \
            paths=[user_job_package_path]):

            self.logger.warning("Not package %s found... creating it.", rez_context_maker.rez_name)

            if not rez_context_maker(path=user_job_package_path):
                self.logger.exception("Somehting went wrong. can't set. %s", OSError)
                raise OSError
        
        r = ResolvedContext(rez_package_names, package_paths=package_paths)

        if r.success:
            r.execute_shell()

        return True
       









      