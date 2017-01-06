from .base import Base

class CreateJobTemplate(Base):
    """ Sub command which performs creation of disk directories
       based on schemas.
    """
 
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
            

        from job.cli import JobTemplate, setup_logger
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
                job = JobTemplate(**kwargs)
                # We need to reinitialize Job() in case we want to find
                # local schemas:
                if not self.options['--no_local_schema']:
                    local_schema_path = job.get_local_schema_path()
                    job.load_schemas(local_schema_path)
                    super(JobTemplate, job).__init__(job.schema, "job", **kwargs)
                job.create()

        return job
 
    def run(self):
        """ Entry point for sub command.
        """

        if self.options['create']:
            job = self.create_command()
        if job and not self.options['--no_local_schema']:
            job.dump_local_templates()







      