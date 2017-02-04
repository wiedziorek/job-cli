from logging import INFO

# https://fangpenlin.com/posts/2012/08/26/good-logging-practice-in-python/
# def setup_logger(name, preference_file = 'logging.json', 
#                        log_level       =  INFO):
#     """ Setup logging configuration.
#     """
#     from os.path import join, split, realpath, dirname, exists
#     import logging.config
#     from json import load

#     _path = dirname(realpath(__file__))
#     _path = join(_path, preference_file)

#     if exists(_path):
#         with open(_path, 'rt') as file:
#             config = load(file)
#         logging.config.dictConfig(config)
#     else:
#         logging.basicConfig(level=log_level)

#     logger = logging.getLogger(name)
#     logger.setLevel(log_level)

#     return logger


def get_log_level_from_options(self, options={}):
    """ This is ugly.
    """
    import logging
    log_level = logging.INFO

    if not "--log-level" in options:
        return log_level

    if not options['--log-level']:
        return log_level

    try:
        log_level = getattr(logging, options['--log-level'])
    except:
        pass   

    return log_level


# http://stackoverflow.com/questions/3237678/how-to-create-decorator-for-lazy-initialization-of-a-property
class ReadOnlyCacheAttrib(object):    
    '''Computes attribute value and caches it in the instance.
    Source: Python Cookbook 
    Author: Denis Otkidach http://stackoverflow.com/users/168352/denis-otkidach
    This decorator allows you to create a property which can be computed once and
    accessed many times. Sort of like memoization
    '''
    def __init__(self, method, name=None):
        self.method = method
        self.name = name or method.__name__
        self.__doc__ = method.__doc__
    def __get__(self, inst, cls): 
        if inst is None:
            return self
        elif self.name in inst.__dict__:
            return inst.__dict__[self.name]
        else:
            result = self.method(inst)
            inst.__dict__[self.name]=result
            return result    
    def __set__(self, inst, value):
        raise AttributeError("This property is read-only")
    def __delete__(self,inst):
        del inst.__dict__[self.name]