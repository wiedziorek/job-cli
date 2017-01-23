
from schematics.models import Model
from schematics.types import StringType, URLType, BooleanType, BaseType
from schematics.types import UUIDType, DateTimeType, TimestampType 
from schematics.types import ListType, ModelType, DictType, PolyModelType
from schematics import exceptions
import json

def isPathTemplateType(value):
    if not '@' in value and not "/>" in value:
        raise exceptions.ValidationError("This doesn't seem to be path template.")


class PathTemplateType(BaseType):

    """A field that stores a valid path expression value.
    """
    MESSAGES = {
        "path_template": "Value must be valid path template expression using @WORD/>",
    }

    # def __init__(self, validators=[isPathTemplateType]):
    #     super(PathTemplateType, self).__init__(validators=validators)

    def validate_pathtemplate(self, value):
        raise exceptions.ValidationError("This doesn't seem to be path template.")
        if not '@' in value or not "/>" in value:
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
        return str(value)

class SchemaInlineModel(Model):
 
    names     = ListType(StringType, required=True)
    # inline_options   = DictType(PolyModelType)


class SchemaModel(Model):
    user_dirs  = BooleanType(required=True) 
    permission = DictType(BooleanType, required=False)
    ownership  = DictType(StringType, required=False)
    job_asset_name = StringType(required=True)
    sub_dirs       = ListType(DictType(StringType), required=False)
    job_asset_type = StringType(required=True)
    names          = ListType(StringType, required=True)
    link_root      = StringType(required=False)
    is_link        = BooleanType(required=True)
    link_target    = PathTemplateType(required=False)
    root           = StringType(required=False)
    job_current    = StringType(required=True)
    path_template  = PathTemplateType(required=False)
    local_schema_path = DictType(PathTemplateType, required=False)

schemafile = '/home/symek/work/job-cli/job/schema/job.schema'
with open(schemafile) as file:
    schema = json.load(file)

print schema
job = SchemaModel(schema)
print json.dumps(job.to_primitive(), indent=4)

# print job.path_template
# tmp = PathTemplateType()


