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
from .base import BaseSubCommand


class JobEnvironment(object):
    """ Renders job environment gathering bits of information from
        JobTemplate created on-the-fly, previuosly saved session,
        or user settings. At the end, we should call execute() to
        teleport ourself into prepered environment.

    """
    cli_options = None
    job_path    = None
    def __init__(self, cli_options, log_level='INFO'):
        """ Copy all settings from cli and what's not.
        """
        from os.path import join
        from os import getenv
        self.cli_options    = cli_options
        self.job_current    = self.cli_options['PROJECT']
        self.job_asset_type = self.cli_options['TYPE']
        self.job_asset_name = self.cli_options['ASSET']
        self.log_level      = log_level

        if self.cli_options['--root']:
            self.root = self.cli_options['--root']
        else:
            self.root = None

        self.job_template = self.__create_job_template()
        self.job_path     = self.job_template.expand_path_template()
        self.user_path    = join(getenv("HOME"), ".job")

        from job.plugin import PluginManager 
        self.plg_manager = PluginManager(log_level=log_level)
        self.env_maker   = self.plg_manager.get_plugin_by_name("RezEnvironment") 


    def find_job_context(self, job_template=None):
        """ Using underlying context creator find if current
            job was previously created (by set command). 

            Parms  : 
                job_template: job_template once again happends to be definite guide to
                project details. This is the only way arbitrarty plugins can handle
                changing naming convension suppored by Job v2.
    
            Returns:  manifestation of the job context 
                      (rez package for example) or None.
        """

        return self.env_maker.find(job_template, self.user_path)


    def __create_job_template(self):
        """ Creates job template instance to trace vital
            information from it (location, naming convension).

            Returns: JobTemplate class instance.
        """
        from job.template import JobTemplate
        # Pack arguments so we can ommit None one (like root):
        kwargs = {}
        kwargs['job_current']    = self.job_current
        kwargs['job_asset_type'] = self.job_asset_type
        kwargs['job_asset_name'] = self.job_asset_name
        kwargs['log_level']      = self.log_level
        if self.root:
            kwargs['root']  = self.root

        job_template = JobTemplate(**kwargs)
        if not self.cli_options['--no-local-schema']:
            local_schema_path = job_template.get_local_schema_path()
            job_template.load_schemas(local_schema_path)
            super(JobTemplate, job_template).__init__(job_template.schema, "job", **kwargs)

        return job_template





class SetEnvironment(BaseSubCommand):
    """ Performs setting up of the environment per job.
    """
 
    def run(self):
        """ Entry point for sub command.
        """
        # from rez.resolved_context import ResolvedContext
        # from rez.packages_ import get_latest_package
        from os.path import join, isdir
        from os import mkdir, getenv
        from job.logger import LoggerFactory

        log_level   = self.cli_options['--log-level']
        self.logger = LoggerFactory().get_logger("SetEnvironment", level=log_level)

        user_job_package_path = join(getenv("HOME"), ".job")
        if not isdir(user_job_package_path):
            mkdir(user_job_package_path)

        job = JobEnvironment(self.cli_options, log_level=log_level)
        job.env_maker(job.job_template)
        print job.env_maker.rez_pkg_name
        # print job.job_template['root']


        # package_paths     = [user_job_package_path] + job.rez_config.packages_path

        # Reading options from command line and saved in job.opt(s)
        # How to make it cleaner?
        # rez_package_names = []
        # # Job option pass:
        # if "--rez" in job.job_template.job_options:
        #     rez_package_names += job.job_template.job_options['--rez']

        # # Command line pass:
        # if self.cli_options['--rez']:
        #     rez_package_names += self.cli_options['--rez']
        # rez_package_names += [job.rez_name]

        # Lets try if packages was already created:
        # if not get_latest_package(job.data['name'], \
        #     range_=job.data['version'], \
        #     paths=[user_job_package_path]):

        #     self.logger.warning("Not package %s found... creating it.", job.rez_name)

        #     if not job(path=user_job_package_path):
        #         self.logger.exception("Somehting went wrong. can't set. %s", OSError)
        #         raise OSError

        # context = ResolvedContext(rez_package_names, package_paths=package_paths)

        # # Finally we might be able to set, but first lets create user dirs,
        # # This should be generalized into pre-set, post-set registerable actions though
        # # Not even sure it should be here at all.
        # if context.success:
        #     locations = job.job_template.render()
        #     for loc in locations:
        #         if locations[loc]['user_dirs']:
        #             user_dir = job.get_user_subdir(loc)
        #             target   = { user_dir: locations[loc] }
        #             job.job_template.create(targets=target)
        #     context.execute_shell()

        # return True
       









      