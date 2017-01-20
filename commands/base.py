


class Base(object):
    """A base command."""
    logger = None
 
    def __init__(self, options, *args, **kwargs):
        self.options = options
        self.args = args
        self.kwargs = kwargs

    def get_log_level_from_options(self, options=None):
        """
        """
        import logging
        log_level = logging.INFO
        # This is ugly, subcommand should extend list of options (like plugin)
        # not rely on bin/job to provide corrent switches.
        _opt = self.options
        if options:
            _opt = options
        if _opt['--log-level']:
            try:
                log_level = getattr(logging, _opt['--log-level'])
            except:
                pass
        return log_level

 
    def run(self):
        raise NotImplementedError('You must implement the run() method yourself!')

