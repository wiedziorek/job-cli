
from schematics.models import Model
from schematics.types import StringType, URLType, BooleanType, BaseType, IntType
from schematics.types import UUIDType, DateTimeType, TimestampType 
from schematics.types import ListType, ModelType, DictType, PolyModelType
from schematics import exceptions

import json
import collections


class PathTemplateType(BaseType):

    """A field that stores a valid path expression value.
    """

    MESSAGES = {
        "path_template": "Value must be valid path template expression using @WORD/>",
    }

    def validate_pathtemplate(self, value):
        #TODO: make it useful
        if not value:
            return
        if not value.startswith("@"): # or not "/>" in value:
            raise exceptions.ValidationError("This doesn't seem to be path template.")

    def _mock(self, context=None):
        return value

    def to_native(self, value, context=None):
        if not isinstance(value, str):
            try:
                value = str(value)
            except (TypeError, ValueError):
                raise ConversionError(self.messages['convert'].format(value))
        return value

    def to_primitive(self, value, context=None):
        """ Shell we actually render template to final shape here?
        """
        return str(value)

class PermissionModel(Model):
    group  = BooleanType(required=False)
    others = BooleanType(required=False)

class OwnershipModel(Model):
    user   = StringType(required=False)
    group  = StringType(required=False) 

class InlineOptionsModel(Model):
    ownership   = ModelType(OwnershipModel, required=False)
    permission  = ModelType(PermissionModel, required=False)
    link_target = PathTemplateType(required=False)

class SchemaInlineModel(Model):
    type        = StringType(required=True)
    name        = StringType(required=True)
    options     = ModelType(InlineOptionsModel, required=False)


class SchemaModel(Model):
    """ Basic model for all LocationTemplates except JobTemplate.
        This was forced by Schamatics and has nice side effects 
        of controlling presence of keys on different levels
        (for a price of generality and elegance).
    """
    version  = StringType(required=True)
    names    = ListType(StringType, required=True)
    sub_dirs = ListType(ModelType(SchemaInlineModel), required=False)

    user_dirs  = BooleanType(required=False) 
    ownership   = ModelType(OwnershipModel, required=False)
    permission  = ModelType(PermissionModel, required=False)
   
   # This must be always presnt of children 
   # will createa own link instead of taking it from parent.
    is_link     = BooleanType(required=True) 
    link_root   = StringType(required=False)
    link_target = PathTemplateType(required=False)
    
    path_template     = PathTemplateType(required=False)
    local_schema_path = DictType(PathTemplateType, required=False)
    root              = StringType(required=False)
    #tmp:
    log_level         = IntType(required=False)



class JobSchemaModel(Model):
    """ Schema model valid only for parent (job) template.
        It has to be separated, so thus some important keys
        like job_current counldn't be overwritten by children
        templates. 
    """
    version  = StringType(required=True)
    names    = ListType(StringType, required=True)
    sub_dirs = ListType(ModelType(SchemaInlineModel), required=False)

    job_current    = StringType(required=True)
    job_asset_type = StringType(required=True)
    job_asset_name = StringType(required=True)

    user_dirs  = BooleanType(required=True) 
    ownership   = ModelType(OwnershipModel)
    permission  = ModelType(PermissionModel)

    is_link     = BooleanType(required=True)
    link_root   = StringType(required=False)
    link_target = PathTemplateType(required=False)
    
    path_template     = PathTemplateType(required=False)
    local_schema_path = DictType(PathTemplateType, required=False)
    root              = StringType(required=False)

    #tmp:
    log_level         = IntType(required=False)



class StaticDict(collections.MutableMapping):
    def __init__(self, data):
        self.__data = data

    def __len__(self):
        return len(self.__data)

    def __iter__(self):
        return iter(self.__data)

    def __setitem__(self, k, v):
        if k not in self.__data:
            raise KeyError(k)

        self.__data[k] = v

    def __delitem__(self, k):
        raise NotImplementedError

    def __getitem__(self, k):
        return self.__data[k]

    def __contains__(self, k):
        return k in self.__data



class Factory(object):
    def find(self, schema, version=None, be_nice=False, verbose=False):
        """ Returns to a caller (LocationTemplate subclasses mostly)
            a validated models made from provided dictonary. Raise 
            exeption if no valid schema could be provided.
        """
       
        # Try first Job schema, it it fails, try child model:
        # This is because some fields are dengeours 
        # (job,group,asset ids mainly)

        # FIXME: how to make it nicely?
        if "job_current" in schema:
            model = JobSchemaModel(schema)
        else:
            model = SchemaModel(schema)
       
        error = None
        error = model.validate()
          
        if not error:
            if verbose:
                print json.dumps(model.to_primitive(), indent=4)
            return StaticDict(model.to_primitive())
       
        if be_nice:
            return StaticDict(schema)

        return None

