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

from job.plugin import PluginManager, PluginType
from importlib import import_module
import os, sys
from glob import glob

REZ_FOUND = False

# Find REZ 
# TODO: We may place it into a class itself for cleaner setup, but
# this is contr-intuitive. Test it.

if not os.getenv("REZ_CONFIG_FILE", None):
    try:
        import rez 
        REZ_FOUND = True
    except ImportError, e:
       pass
else:
    rez_path = os.environ['REZ_CONFIG_FILE']
    rez_path = os.path.dirname(rez_path)
    rez_candidate = os.path.join(rez_path, "lib64/python2.7/site-packages/rez-*.egg")
    rez_candidate = glob(rez_candidate)
    if rez_candidate:
        sys.path.append(rez_candidate[0])
        import rez 
        REZ_FOUND = True


class NoJobTemplateSet(Exception):
    """This environment has no job template set yet."""



class RezEnvironment(PluginManager):
    name    = "RezEnvironment"
    type    = PluginType.Environment
    __data  = {}
    logger  = None
    rez_config      = None
    rez_pkg         = None
    rez_pkg_name    = None
    rez_pkg_version = None
    job_template    = None
    rez_package     = None

    def register_signals(self):
        """ Find REZ. We might consider making it citizense of job-cli.
        """
        
        if REZ_FOUND:
            self.logger.debug("%s registering as %s", self.name, self.type)
        else:
            self.logger.exception("Cannot import rez. Rez based plugins won't work, %s", e)
        return REZ_FOUND


    def find_context(self, job_template=None, version=None, path=None):
        """ Find rez package based on provided job_template range
            in provided path.
        """
        from rez.packages_ import get_latest_package

        if not job_template and not self.job_template:
            raise NoJobTemplateSet("Can't find context without job_template argumenet, \
                while it wasn't bind previously.")

        # WARNING: We do not rebind new job_template here!
        # User might want to find other context not currently bind.
        if not job_template:
            job_template = self.job_template

        # If above is the case, we have to take care of items assigments too
        # (to not to polute self with ad-hoc searches...)
        rez_pkg, rez_pkg_name, rez_pkg_version =\
             self.__create_rez_names(job_template)

        if job_template == self.job_template:
            self.rez_pkg         = rez_pkg
            self.rez_pkg_name    = rez_pkg_name
            self.rez_pkg_version = rez_pkg_version

        if path:
            return get_latest_package(rez_pkg, range_=rez_pkg_version, paths=[path])
        else:
            return get_latest_package(rez_pkg, range_=rez_pkg_version)


    def __call__(self, job_template):
        """ This is only to stay in sync with other plugins theme,
            which usually run on object.__call__().
        """
        self.init(job_template)
        

    def init(self, job_template):
        """ Initialize Rez specific local variables ...
        """

        from os.path import join, expanduser
        from rez import config

        self.job_template = job_template
        self.rez_config   = config.create_config()

        self.rez_pkg, self.rez_pkg_name, self.rez_pkg_version =\
             self.__create_rez_names(job_template)

        self.local_pkg_path = join(expanduser("~"), ".job")
        self.packages_path  = [self.local_pkg_path] + self.rez_config.packages_path
     

    def create_context(self, path=None, install=True):
        """ Creates ad-hoc Rez package that will serve as job context resolver.
            Packages will be saved in ~/.job directory and used in execute_context().

            Parms:
                paths  : overrites default install path
                install: install package after creation

            Returns:
                Rez package object or False on failure.
        """
        from os.path import expanduser, join
        from rez import packages_

        if not self.job_template:
            raise NoJobTemplateSet("Can't create context without job_template bind previously.")
        template = self.job_template

        # TODO: Find more general way of creating environment. 
        # This should be driven by abstract interface with plugin 
        # implementation.
        commands = self.__create_env_commands(
            (('JOB_CURRENT',    template['job_current']), 
             ('JOB_ASSET_TYPE', template['job_asset_type']),
             ('JOB_ASSET_NAME', template['job_asset_name']),
             ('JOB',            template.expand_path_template())
             )
        )

        self.__data = {'version': self.rez_pkg_version, 'name': self.rez_pkg, 
                'uuid'   : 'repository.%s' % self.rez_pkg, 'variants':[], 'commands': commands}

        if not path:
           path = self.local_pkg_path
    
        package = self.__create_rez_package(self.__data)

        if not package:
            return False

        self.rez_package = package

        if install:
            self.__install_rez_package(package, path)

        return package


    def execute_context(self, packages=[]):
        """ Execute Rez context with provided packages.

            Parms:
                packages: list of packages to resolve in context.
                Empy list means we'd like to run only previously created job context.

            Returns:
                False on context resolution failure, True overwise.
        """
        from rez.resolved_context import ResolvedContext

        requested = [self.rez_pkg_name]

        assert (isinstance(packages, list))

        if packages:
            requested += packages

        context = ResolvedContext(requested, package_paths=self.packages_path)

        if context.success:
            context.execute_shell()
            return True
        return False


    def __create_rez_names(self, job_template):
        """ Creates identifies sufficient for Rez to create or find and load
            created previously packages.

            Parm: 
                job_template: JobTemplate instance of current job
            Return:
                package, full name, version: strings required by Rez to create and load pkg.
        """
        from os.path import sep

        #  Since nobody knows what naming convension given job is using 
        # (except job_template which should be expressive enought to 
        # derive this information from it), we have to establish some
        #  convension for ourself here.

        # FIXME: We will have to revisit here, once we will have proper
        # variable expansion inside LocationTemplate (via Schema probably.)
        
        asset_id_template = job_template['asset_id_template']
        extended = job_template.expand_path_template(asset_id_template)
        elements = extended.split(os.sep)

        rez_pkg         = elements[0]
        rez_pkg_name    = "-".join(elements)
        rez_pkg_version = "-".join(elements[1:])

        return rez_pkg, rez_pkg_name, rez_pkg_version 


    def __create_env_commands(self, args, expression='export %s=%s'):
        """ Helper to warp tuples in bash commands.

            Parms: 
                args   : tuple of tupls ((x, v, ...))
                command: command to expand tuple with. 
        """
        commands = []
        for v in args:
            assert len(v) == expression.count("%")
            commands += [expression % tuple(v)]
        return commands


    def __create_rez_package(self, data):
        """ Creates rez package from data.

            Parm: dictionary consisting of: 
                version - rez ver. string (X.Y-Z)
                name    - string,
                uuid    - string (usually repository.id) 
                variants- list 
                commands- list of bash commands (TODO: new style) 
        """
        from rez.packages_ import create_package
        package = create_package(data['name'], data)
        return package


    def __install_rez_package(self, package, path):
        """ Install rez package into a path.

            Parm: valid path to place rez package into.
        """
        variant = package.get_variant()
        variant.install(path)

    def context_name(self, job_template=None):
        """
        """
        if not job_template and not self.job_template:
            raise NoJobTemplateSet("JobTemplate has to be specified first.")

        if not job_template:
            job_template = self.job_template

        if None in [self.rez_pkg, self.rez_pkg_name, self.rez_pkg_version]:
            return self.__create_rez_names(job_template)
        else:
            return self.rez_pkg, self.rez_pkg_name, self.rez_pkg_version