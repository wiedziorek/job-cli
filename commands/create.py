from .base import BaseSubCommand

class CreateJobTemplate(BaseSubCommand):
    """ Sub command which performs creation of disk directories
       based on schemas.
    """

    def create_job_asset_range(self, job_asset_name, number_mult=10, zeros=4):
        """ Generates a list of asset names from asset name expression:
            asset_name[1-10]

            Params:
                asset_name = 'shot[1-10]' ('shot0010' which won't be expanded.)

            Returns:
                list = [base0010, base0020, ....]
        """

        def parse_asset_name(name):
            """ Parse asset name or asset group for patterns asset[1-2]
            """
            import re
            expression = re.compile('\[([0-9]+)-([0-9]+)\]$')
            sequence   = expression.findall(name)
            if sequence:
                return [int(x) for x in list(sequence[0])]
            return []

        job_asset_name_list = []
        job_asset_range = parse_asset_name(job_asset_name)
        assert not job_asset_range or len(job_asset_range) == 2

        # !!! inclusive 
        if len(job_asset_range) == 2:
            job_asset_range[1] += 1 # !!!

        if job_asset_range:
            job_asset_base = job_asset_name.split("[")[0] # Correct assumption?
            for asset_num in range(*job_asset_range):
                # Should we allow to customize it? Place for preferences?
                asset_num *= number_mult
                new_job_asset_name = job_asset_base + str(asset_num).zfill(zeros)
                job_asset_name_list += [new_job_asset_name]

        else:
            job_asset_name_list += [job_asset_name]

        return job_asset_name_list
 
    def create_job(self, project, type_, asset, root, no_local_schema, log_level, dry_run=False):  
        """ Creates a number of insances of JobTemplates, and executes 
            its create() command to render disk locations.
            Allows for bulk execution of expression based asset names.

            Params:
                project, type, asset, root: to pass to JobTemplate class.
        """
        from copy import deepcopy
        from job.template import JobTemplate
        from os import environ

        # Pack arguments so we can ommit None one (like root):
        # Should we standarize it with some class?
        job    = None
        kwargs = {}
        kwargs['job_current']    = project
        kwargs['job_asset_type'] = type_
        kwargs['job_asset_name'] = asset
        kwargs['log_level']      = log_level
        kwargs['root']           = root if root else None
       
            
        # Assets may contain range expression which we might want to expand:
        type_range  = self.create_job_asset_range(type_, number_mult=1, zeros=2)
        asset_range = self.create_job_asset_range(asset)
       
        for group in type_range:
            kwargs['job_asset_type'] = group
            for asset in asset_range:
                kwargs['job_asset_name'] = asset
                job = JobTemplate(**kwargs)
                # We need to reinitialize Job() to find local schemas:
                # This is contr-intuitive as this is most common case, not exeption.
                if not no_local_schema:
                    local_schema_path = job.get_local_schema_path()
                    job.load_schemas(local_schema_path)
                    super(JobTemplate, job).__init__(job.schema, "job", **kwargs)
                # We may want to create jobtemplate without executing it.
                if not dry_run and not job.exists():
                    job.create()

        return job
 
    def run(self):
        """ Entry point create job command. 
        """
        from copy import deepcopy
        import plugins
        from job.logger import LoggerFactory
        from job.plugin import PluginManager

        log_level        = self.cli_options['--log-level']
        self.logger      = LoggerFactory().get_logger("CreateJobTemplate", level=log_level)
        self.plg_manager = PluginManager(self.cli_options['--log-level'])
    
        project = self.cli_options['PROJECT']
        type_   = self.cli_options['TYPE']
        asset   = self.cli_options['ASSET']
        log_lev = self.cli_options['--log-level']
        no_local= self.cli_options['--no-local-schema']
        root    = self.cli_options['--root']
        sanitize= self.cli_options['--sanitize']

        
        # Usual path without database pull. 
        if not self.cli_options['--fromdb']:

            # Create root asset just in case (project/project/project)
            job = self.create_job(project, project, project, root, no_local, log_lev, dry_run=True)
            if not job.exists():
                job.create()
                if not no_local: 
                    job.dump_local_templates()
            else:
                self.logger.warning("Job already exists. Needs update? %s", \
                    "/".join([project, project, project]))

            # Proceed with assets if specified in cli (asset and type_ may contain range expressions)
            if type_ and asset:
                job = self.create_job(project, type_, asset, root, no_local, log_lev)

        else:
            # This is database path
            self.db_driver = self.plg_manager.get_plugin_by_name("ShotgunReader") 
            project_items  = self.db_driver.get_project_items(project, sanitize=sanitize)
            job = self.create_job(project, project, project, root, no_local, log_lev, dry_run=True)

            if not job.exists():
                job.create()
                if not no_local:
                    job.dump_local_templates() 

            for item in project_items:
                if not item['job_asset_name'] or not item['job_asset_type']:
                    self.logger.warning("Database item missing data, can't create it: %s", str(item))
                    continue
                type_ = item['job_asset_type']
                asset = item['job_asset_name']
                job = self.create_job(project, type_, asset, root, no_local, log_lev)







      