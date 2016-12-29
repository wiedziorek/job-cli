from .base import Base

class CreateJobTemplate(Base):
    """ Sub command which performs creation of disk directories
       based on schemas.
    """
 
    def run(self):
        from job.cli import Job
        from logging import DEBUG, INFO
        
        if self.options['create']:
            job_name  = self.options['PROJECT']
            job_group = self.options['TYPE']
            job_asset = self.options['ASSET']

            if not job_group or not job_asset:
                job_group = job_name
                job_asset = job_name

            job = Job(job_name  = job_name, 
                      job_group = job_group, 
                      job_asset = job_asset, 
                      log_level = INFO, 
                      root      = '/tmp/dada')

            job.create()
            job.dump_local_templates()
      