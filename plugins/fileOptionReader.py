from job.plugin import PluginManager, PluginType



class FileOptionReader(PluginManager):
    name = "FileOptionReader"
    type = PluginType.OptionReader
        
    def register_signals(self):
        print "I am %s and register as the %s" % (self.name, self.type)

    def load_options_from_file(self, path, options={}):
        """
        """
        from glob import glob
        from os.path import join, split, splitext
        import json
        files = []
        for postfix in self.job.JOB_PATH_POSTFIX:
            path     = join(path, postfix)
            location = join(path, "*.%s" % self.job.OPTION_FILE_EXTENSION)
            files    += glob(location)

        self.job.logger.debug("Options found: %s", files)

        for file in files:
            with open(file) as file_object:
                obj  = json.load(file_object)
                for k, v in obj.items():
                    options[k] = v
        return options

    def __call__(self, jobtemplate):
        self.job = jobtemplate
        import job.cli # Just to find job/schema/* location
        from os.path import join, split, realpath, dirname

        options_paths = [dirname(realpath(job.cli.__file__))]
        options_paths += self.job.get_local_schema_path()
        options = {}

        for path in options_paths:
            opt = self.load_options_from_file(path)
            for k, v in opt.items():
                options[k] = v
        return options