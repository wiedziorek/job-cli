from .base import Base

class CreateJobTemplate(Base):
    """ Sub command which performs creation of disk directories
       based on schemas.
    """
    job = None
    def get_log_level(self):
        """
        """
        import logging
        log_level = logging.INFO
        # This is ugly, csubcommand should extend list of options (like plugin)
        # not rely on bin/job to provide corrent switches. 
        if self.options['--log_level']:
            try:
                log_level = getattr(logging, self.options['--log_level'])
            except:
                pass
        return log_level
 
    def create_command(self):  
        """
        """     
        from job.cli import Job
        log_level = self.get_log_level()
        job_name  = self.options['PROJECT']
        job_group = self.options['TYPE']
        job_asset = self.options['ASSET']

        if self.options['--root']:
            root = self.options['--root']
        else:
            root = '/tmp/dada'

        if not job_group or not job_asset:
            job_group = job_name
            job_asset = job_name

        self.job = Job(job_name  = job_name, 
                      job_group = job_group, 
                      job_asset = job_asset, 
                      log_level = log_level, 
                      root      = root)

        self.job.create()
 
    def run(self):

        if self.options['create']:
            self.create_command()
        if self.job and not self.options['--no_local_schema']:
            self.job.dump_local_templates()
      