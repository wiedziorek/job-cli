from .base import Base

class CreateJobTemplate(Base):
    """ Sub command which performs creation of disk directories
       based on schemas.
    """
    job    = None
    logger = None

    def get_log_level_from_options(self):
        """
        """
        import logging
        log_level = logging.INFO
        # This is ugly, subcommand should extend list of options (like plugin)
        # not rely on bin/job to provide corrent switches. 
        if self.options['--log_level']:
            try:
                log_level = getattr(logging, self.options['--log_level'])
            except:
                pass
        return log_level

    def get_local_schemas(self):
        """ Once we know where to look for we may want to refer to
            local schema copy if the job/group/asset, as they might
            by edited independly from defualt schemas or any other
            present in environ varible JOB_TEMPLATE_PATH.

            Parms : job - object to retrieve local_schema_path templates.
            Return: list of additional schema locations 
        """
        assert self.job
        # This is ugly, should we move it to Job()?
        job_schema   = self.job['local_schema_path']['job']
        group_schema = self.job['local_schema_path']['group']
        asset_schema = self.job['local_schema_path']['asset']

        local_schema_path  = [self.job.expand_path_template(template=job_schema)]
        local_schema_path += [self.job.expand_path_template(template=group_schema)]
        local_schema_path += [self.job.expand_path_template(template=asset_schema)]

        return local_schema_path
 
    def create_command(self):  
        """
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

        def create_job_asset_range(job_asset_name, number_mult=10, zeros=4):
            """ Generates a list of asset names from asset name expression:
                asset_name[1-10]

                Params:
                    asset_name = 'shot[1-10]' ('shot0010' which won't be expanded.)

                Returns:
                    list = [base0010, base0020, ....]
            """
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
            

        from job.cli import Job, setup_logger, JOB_TEMPLATE_PATH_ENV
        from os import environ
        log_level = self.get_log_level_from_options()

        job_name  = self.options['PROJECT']
        job_group = self.options['TYPE']
        job_asset = self.options['ASSET']

        if self.options['--root']:
            root = self.options['--root']
        else:
            root = None

        if not job_group or not job_asset:
            job_group = job_name
            job_asset = job_name


        # Pack arguments so we can ommit None one (like root):
        kwargs = {}
        kwargs['job_name']  = job_name
        kwargs['job_group'] = job_group
        kwargs['log_level'] = log_level
        if root:
            kwargs['root']  = root

        # Asset may contain range expression which we might want to expand:
        job_group_range = create_job_asset_range(job_group, number_mult=1, zeros=2)
        job_asset_range = create_job_asset_range(job_asset)

        for group in job_group_range:
            kwargs['job_group'] = group
            for asset in job_asset_range:
                kwargs['job_asset'] = asset
                self.job = Job(**kwargs)
                # We need to reinitialize Job() in case we want to find
                # local schemas:
                if not self.options['--no_local_schema']:
                    local_schema_path = self.get_local_schemas()
                    self.job.load_schemas(local_schema_path)
                    super(Job, self.job).__init__(self.job.schema, "job", **kwargs)
                self.job.create()
 
    def run(self):
        from job.cli import Job
        # self.logger = setup_logger("Job", self.get_log_level())


        if self.options['create']:
            self.create_command()
        if self.job and not self.options['--no_local_schema']:
            self.job.dump_local_templates()







      