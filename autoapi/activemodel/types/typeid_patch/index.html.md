# activemodel.types.typeid_patch

Add pydantic v2 support for TypeID.

* The TypeID package has a TypeIDField[Literal[“prefix”]] support, but this is not a subclass of TypeID
  which causes errors when a TypeID object is assigned to a field of that type.
* TypeIDField generates a unique type and embeds the prefix in the type, which is how how the instance of the object
  can validate incoming strs as having the correct prefix.
* This isn’t exactly required in our case since the prefix validation is handled within the SQLAlchemy type adapter.
* However,

## Attributes

| [`existing_schema`](#activemodel.types.typeid_patch.existing_schema)           |    |
|--------------------------------------------------------------------------------|----|
| [`existing_json_schema`](#activemodel.types.typeid_patch.existing_json_schema) |    |

## Module Contents

### *classmethod* activemodel.types.typeid_patch.get_pydantic_core_schema(source_type: Any, handler: [pydantic.GetCoreSchemaHandler](https://pydantic.dev/docs/validation/latest/api/pydantic/annotated_handlers/#pydantic.annotated_handlers.GetCoreSchemaHandler)) → pydantic_core.CoreSchema

### *classmethod* activemodel.types.typeid_patch.get_pydantic_json_schema(core_schema_: pydantic_core.CoreSchema, handler: [pydantic.GetJsonSchemaHandler](https://pydantic.dev/docs/validation/latest/api/pydantic/annotated_handlers/#pydantic.annotated_handlers.GetJsonSchemaHandler)) → pydantic.json_schema.JsonSchemaValue

### activemodel.types.typeid_patch.existing_schema

### activemodel.types.typeid_patch.existing_json_schema
