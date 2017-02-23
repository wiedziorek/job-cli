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


class NoJobEnvironmentBackend(Exception):
    """ Raised when JobEnvironment can't find requested backend plugin."""

class SetCommandNotSuccessful(Exception):
    """ Set command could not be performed. Leaving in current shell."""


class JobEnvironment(object):
    """ Renders job environment gathering bits of information from
        JobTemplate created on-the-fly, previuosly saved session,
        or user settings. At the end, we should call execute() to
        teleport ourself into prepered environment.

    """
    cli_options = None
    job_path    = None
    def __init__(self, cli_options=None, log_level='INFO'):
        """ Copy all settings from cli and creates job template class from
            a description. Also initialize environment plugin, saves it as 
            a backend object to be used for something usefull.
        """
        from os import mkdir
        from os.path import join, expanduser, isdir
        from job.plugin import PluginManager
        from job.logger import LoggerFactory 
        import plugins

        self.log_level    = log_level
        self.logger       = LoggerFactory().get_logger("JobEnvironment", level=log_level)
        self.plg_manager  = PluginManager(log_level=log_level)
        self.package_path = join(expanduser("~"), ".job")

        if not isdir(self.package_path):
            self.logger.debug("No ~/.job directory. Creating it.")
            mkdir(self.package_path)

        # TODO: Make it configurable
        environ_plugin_name = "RezEnvironment"
        self.backend = self.plg_manager.get_plugin_by_name(environ_plugin_name) 

        # This is in case, we will be asking for plugin type rather then by name,
        # so plugin manager might not catch missing one.
        if not self.backend:
            message = "Can't operate without environment backend %s"
            self.logger.exception(message, environ_plugin_name)
            raise NoJobEnvironmentBackend(message % environ_plugin_name)

        if cli_options:
            self.init(cli_options)

    def init(self, cli_options, history=True):
        """ Make all steps requireing cli_options. We might saved this dict
            in history, so not always command line is what we are after. 
        """
        from os.path import join, expanduser, isdir
        from os import mkdir
        from json import dumps

        self.cli_options    = cli_options
        self.job_current    = self.cli_options['PROJECT']
        self.job_asset_type = self.cli_options['TYPE']
        self.job_asset_name = self.cli_options['ASSET']

        if self.cli_options['--root']:
            self.root = self.cli_options['--root']
        else:
            self.root = None

        self.job_template = self.__create_job_template()
        self.job_path     = self.job_template.expand_path_template()

        # Bind (init) job context tp the job_template:
        self.backend(self.job_template)

        if not history or not self.job_current:
            return
            
        # Save history:
        history_folder = join(self.package_path, self.job_current)
        if not isdir(history_folder):
            mkdir(history_folder)

        with open(join(history_folder, "job.history"), 'w') as file:
            file.write(dumps(self.cli_options))
        with open(join(self.package_path, "job.history"), 'w') as file:
            file.write(dumps(self.cli_options))


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

        if job_template:
            _template = job_template
        else:
            _template = self.job_template

        return self.backend.find_context(_template, path=self.package_path)


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

    def create_user_dirs(self, user=None):
        """ Verb using job template to create user subdir.
            TODO: This should be moved to JobTemplate class.
        """
        from getpass import getuser
        from os.path import join

        if not user:
            user = getuser()

        template = self.job_template.render()

        for path in template:
            if template[path]['user_dirs']:
                user_dir = join(path, user)
                target   = { user_dir: template[path] }
                ok = self.job_template.create(targets=target)
                if not ok:
                    return
        return ok

    def get_history_from_file(self, cli_options):
        """ Finds historic cli_options to recreate JobEnvironment based on 
            saved information (mostly job_current, job_asset_type, job_asset_name).

            There are two histories suppored: 
                    a) last set on any project: job set 
                    b) last set to specified project: job set PROJECT [rest arg is ignored]

            Parms: 
                cli_options: current cli_options (possibly no args)

            Return: 
                retrieved from history cli_options
        """
        from os.path import isfile, join
        from json import load

        if not cli_options['PROJECT']:
            history_folder = self.package_path
        else:
            history_folder = join(self.package_path, cli_options['PROJECT'])

        history_file = join(history_folder, "job.history")

        if not isfile(history_file):
            self.logger.debug("No history file: %s", history_file)
            return None

        with open(history_file) as file:
            try:
                cli_options = load(file)
                self.logger.debug("Reading cli_options from file: %s", history_file)
            except IOError, e:
                self.logger.exception("Can't read history from %s", history_file)
                return None

        return cli_options


class SetEnvironment(BaseSubCommand):
    """ Performs setting up of the environment per job.
    """
 
    def run(self):
        """ Entry point for sub command.
        """
        from os.path import join, isdir, expanduser
        from job.logger import LoggerFactory

        log_level   = self.cli_options['--log-level']
        self.logger = LoggerFactory().get_logger("SetEnvironment", level=log_level)
        job         = JobEnvironment(log_level=log_level)

        # Lack of PROJECT or ASSET specification triggers reading history file
        if None in (self.cli_options['PROJECT'], self.cli_options['TYPE'], self.cli_options['ASSET']):

            # Can't deal with both missing args and refreshing...
            if self.cli_options['--refresh']:
                self.logger.exception("Can't set with Refresh and missing arguments, ")
                raise SetCommandNotSuccessful("Either remove --refresh flag or specify project type asset. ")

            cli_options = job.get_history_from_file(self.cli_options)

            if cli_options:
                self.cli_options = cli_options
            else:
                self.logger.exception("Can't set to the job context. Try to set using: job set PROJECT TYPE ASSET --refresh ")
                raise SetCommandNotSuccessful

        # Postponed initlilization:
        job.init(self.cli_options) 

        # Read additional packages from command line:
        rez_package_names = []
        if self.cli_options['--rez']:
            rez_package_names += self.cli_options['--rez']

        # ...some might be also added in job.options:
        if "--rez" in job.job_template.job_options:
            rez_package_names += job.job_template.job_options['--rez']

        ok  = job.find_job_context()

        # Either this is first set to this asset or we want to refresh its definition:
        if not ok or self.cli_options['--refresh']:
            context_name, package_name, package_version = job.backend.context_name()
            self.logger.warning("Not package %s found... creating it.", package_name)
            ok = job.backend.create_context(requires=rez_package_names, custom={'test':'test'})

        if ok:
            try:
                job.create_user_dirs()
                job.backend.execute_context(rez_package_names)
            except Exception, e:
                self.logger.exception("Can't set to the job context, ", e)
                raise SetCommandNotSuccessful(e)

        else:
            self.logger.info("Can't set to job. Exiting.")


       









      