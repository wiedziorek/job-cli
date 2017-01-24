

class DeviceDriver():
    """ Abstract class defining an interface to production storage.
        Basic implementation does simply local storage manipulation via
        shell or Python interface. More interesitng implementations
        include remote execution or fuse virtual file systems.
    """
    # __metaclass__ = abc.ABCMeta
    # @abc.abstractmethod
    def make_dir(self, path):
        raise NotImplementedError('You must implement the run() method yourself!')
    # @abc.abstractmethod
    def make_link(self, path, targets):
        raise NotImplementedError('You must implement the run() method yourself!')
    # @abc.abstractmethod
    def remove_write_permissions(self, path):
        raise NotImplementedError('You must implement the run() method yourself!')
    # @abc.abstractmethod
    def add_write_permissions(self, path, group=True, others=False):
        raise NotImplementedError('You must implement the run() method yourself!')
    # @abc.abstractmethod
    def set_ownership(self, path, user=None, group=None):
        raise NotImplementedError('You must implement the run() method yourself!')