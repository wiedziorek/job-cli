from job.plugin import PluginManager, PluginType


class RezEnvironment(PluginManager):
    name    = "RezEnvironment"
    type    = PluginType.Environment
    __data  = {}
    logger  = None

    def register_signals(self):
        """ Find REZ. We might consider making it citizense of job-cli.
        """
        import sys, os
        from glob import glob
        self.rez = None

        if not os.getenv("REZ_CONFIG_FILE", None):
            try:
                import rez
            except ImportError, e:
                self.logger.exception("Cannot import rez. Rez based plugins won't work, %s", e)
                return False
        else:
            rez_path = os.environ['REZ_CONFIG_FILE']
            rez_path = os.path.dirname(rez_path)
            rez_candidate = os.path.join(rez_path, "lib64/python2.7/site-packages/rez-*.egg")
            rez_candidate = glob(rez_candidate)
            if rez_candidate:
                sys.path.append(rez_candidate[0])
                import rez
                self.rez = rez
            else:
                self.logger.exception("Cannot import rez. Rez based plugins won't work, %s", e)
                return False

        self.logger.debug("%s registering as %s", self.name, self.type)

        if self.rez:
            import rez.packages_
            from rez.packages_ import get_latest_package
            self.get_latest_package = get_latest_package
            self.rez_config = rez.config
            return True

        return None

    def find(self, job_tempate, version=None, path=None):
        """ Find rez package based on provided job_template range
            in provided path.
        """
        name = "%s-%s-%s" % (job_template['job_current'], 
                             job_template['job_asset_type'], \
                             job_template['job_asset_name'])
        
        version = "%s-%s" % (job_template['job_asset_type'], 
                             job_template['job_asset_name'])


        if path:
            return get_latest_package(name, range_=version, paths=[path])
        else:
            return get_latest_package(name, range_=version)


    def __call__(self, job_template):
        """
        """
        
        self.config =  self.rez_config.create_config()

        self.rez_pkg_name, self.rez_pkg_version =\
             self.__create_rez_names(job_template)



        commands = self.__create_env_exports((('JOB_CURRENT',  job_template['job_current']), 
                                            ('JOB_ASSET_TYPE', job_template['job_asset_type']),
                                            ('JOB_ASSET_NAME', job_template['job_asset_name']),
                                            ('JOB',            job_template.expand_path_template())
                                            ))


        data = {'version': self.rez_version, 'name': self.job_current, 
                'uuid'   : 'repository.%s' % self.job_current,
                'variants':[],
                'commands': commands}

        self.data = data

        # if self.__create_rez_package(self.data):
        #     self.__install_rez_package(path)
        #     return True
        # return False

    def __create_rez_names(self, job_template):
        """ Creates identifies sufficient for Rez to create or find and load
            created previously packages.

            Parm: 
                job_template: JobTemplate instance of current job
            Return:
                name, version: strings required by Rez to create and load pkg.
        """

        #  Since nobody knows what naming convension given job is using 
        # (except job_template which should be expressive enought to 
        # derive this information from it), we have to establish some
        #  convension for ourself here.

        # FIXME: We will have to revisit here, once we will have proper
        # variable expansion inside LocationTemplate (via Schema probably.)
        from os.path import sep
        asset_id_template = job_template['asset_id_template']
        extended = job_template.expand_path_template(asset_id_template)
        elements = extended.split(os.sep)
        rez_name    = "-".join(elements)
        rez_version = "-".join(elements[1:])
        return rez_name, rez_version


    def __create_env_commands(self, args, expression='export %s=%s'):
        """ Helper to warp tuples in bash commands.

            Parms: 
                args   : tuple of tupls ((x, v, ...))
                command: command to expand tuple with. 
        """
        commands = []
        for v in name_values:
            assert len(v) == expression.count("%")
            commands += [expression % tuple(v)]
        return commands

    def __append_user_subdir(self, path, user=None):
        """ Helper appending user name at the 
            end of the path.

            Parm: string path 
        """
        from getpass import getuser
        from os.path import join
        if not user:
            user = getuser()
        return join(path, user)

    def __create_rez_package(self, data):
        """ Creates rez package from data.

            Parm: dictionary consisting of: 
                version - rez ver. string (X.Y-Z)
                name    - string,
                uuid    - string (usually repository.id) 
                variants- list 
                commands- list of bash commands (TODO: new style) 
        """
        from self.rez.packages_ import create_package
        self.package = create_package(data['name'], data)
        return self.package

    def __install_rez_package(self, path):
        """ Install rez package into a path.

            Parm: valid path to place rez package into.
        """
        variant = self.package.get_variant()
        variant.install(path)