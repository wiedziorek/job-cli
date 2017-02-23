import collections
import functools

# TODO: remove it.
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

#https://wiki.python.org/moin/PythonDecoratorLibrary#Memoize
# TODO: Support list arguments (whcih are not hashable
# so we can't use it with this class)
class CachedMethod(object):
   """
        Decorator. Caches a function's return value each time it is called.
        If called later with the same arguments, the cached value is returned
        (not reevaluated).
        Example:
            @CachedMethod
            def fibonacci(n):
               "Return the nth fibonacci number."
               if n in (0, 1):
                  return n
               return fibonacci(n-1) + fibonacci(n-2)
            print fibonacci(12)
   """
   def __init__(self, func):
      self.func = func
      self.cache = {}

   def __call__(self, *args):
      _args = tuple(args)
      if not isinstance(_args, collections.Hashable):
         # uncacheable. a list, for instance.
         # better to not cache than blow up.
         return self.func(*_args)
      if _args in self.cache:
         return self.cache[_args]
      else:
         value = self.func(*_args)
         self.cache[_args] = value
         return value

   def __repr__(self):
      '''Return the function's docstring.
      '''
      return self.func.__doc__

   def __get__(self, obj, objtype):
      '''Support instance methods.
      '''
      return functools.partial(self.__call__, obj)



# http://stackoverflow.com/questions/3237678/how-to-create-decorator-for-lazy-initialization-of-a-property
class ReadOnlyCacheAttrib(object):    
    ''' 
        Computes attribute value and caches it in the instance.
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