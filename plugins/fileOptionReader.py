from job.plugin import PluginManager, PluginType



class FileOptionReader(PluginManager):
    name = "FileOptionReader"
    type = PluginType.OptionReader
        
    def register_signals(self):
        self.logger.debug("%s registering as %s", self.name, self.type)
        return True

    def load_from_file(self, path, extension, options={}):
        """ TODO: Make use of Schematics to very our files
            follow any known convension...
        """
        def _from_json(json_object):
            tmp = {}                                 
            if isinstance(json_object, dict):
                for k in json_object:
                    tmp[k] = _from_json(json_object[k])
            if isinstance(json_object, list):
                return tuple(json_object)
            return tmp

        from glob import glob
        from os.path import join, split, splitext
        import json
        files = []
        for postfix in self.job.JOB_PATH_POSTFIX:
            path     = join(path, postfix)
            location = join(path, "*.%s" % extension)
            files    += glob(location)

        self.job.logger.debug("Options found: %s", files)

        for file in files:
            with open(file) as file_object:
                obj  = json.load(file_object)
                for k, v in obj.items():
                    # This is for caching and safeness
                    if isinstance(v, list):
                        v = tuple(v)
                    options[k] = v
        return options

    def __call__(self, jobtemplate, extension=None):
        self.job = jobtemplate
        import job.cli # Just to find job/schema/* location
        from os.path import join, split, realpath, dirname

        if not extension:
            extension = self.job.OPTION_FILE_EXTENSION

        options_paths = [dirname(realpath(job.cli.__file__))]
        options_paths += self.job.get_local_schema_path()
        options = {}

        for path in options_paths:
            opt = self.load_from_file(path, extension=extension)
            for k, v in opt.items():
                options[k] = v
        return options