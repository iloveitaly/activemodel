# activemodel.types

## Submodules

* [activemodel.types.sqlalchemy_protocol](sqlalchemy_protocol/index.md)
* [activemodel.types.typeid](typeid/index.md)
* [activemodel.types.typeid_patch](typeid_patch/index.md)

## Classes

| [`TypeIDType`](#activemodel.types.TypeIDType)   | A SQLAlchemy TypeDecorator that allows storing TypeIDs in the database.   |
|-------------------------------------------------|---------------------------------------------------------------------------|

## Package Contents

### *class* activemodel.types.TypeIDType(prefix: [str](https://docs.python.org/3/library/stdtypes.html#str), \*args, \*\*kwargs)

Bases: [`sqlalchemy.types.TypeDecorator`](https://docs.sqlalchemy.org/en/20/core/custom_types.html#sqlalchemy.types.TypeDecorator)

A SQLAlchemy TypeDecorator that allows storing TypeIDs in the database.

The prefix will not be persisted to the database, instead the database-native UUID field will be used.
At retrieval time a TypeID will be constructed (in python) based on the configured prefix and the UUID
value from the database.

For example:

```pycon
>>> id = mapped_column(
>>>     TypeIDType("user"),
>>>     primary_key=True,
>>>     default=lambda: TypeID("user")
>>> )
```

Will result in TypeIDs such as “user_01h45ytscbebyvny4gc8cr8ma2”. There’s a mixin provided to make it easy
to add a id pk field to your model with a specific prefix.

#### impl

#### cache_ok *= True*

Indicate if statements using this `ExternalType` are “safe to
cache”.

The default value `None` will emit a warning and then not allow caching
of a statement which includes this type.   Set to `False` to disable
statements using this type from being cached at all without a warning.
When set to `True`, the object’s class and selected elements from its
state will be used as part of the cache key.  For example, using a
`TypeDecorator`:

```default
class MyType(TypeDecorator):
    impl = String

    cache_ok = True

    def __init__(self, choices):
        self.choices = tuple(choices)
        self.internal_only = True
```

The cache key for the above type would be equivalent to:

```default
>>> MyType(["a", "b", "c"])._static_cache_key
(<class '__main__.MyType'>, ('choices', ('a', 'b', 'c')))
```

The caching scheme will extract attributes from the type that correspond
to the names of parameters in the `__init__()` method.  Above, the
“choices” attribute becomes part of the cache key but “internal_only”
does not, because there is no parameter named “internal_only”.

The requirements for cacheable elements is that they are hashable
and also that they indicate the same SQL rendered for expressions using
this type every time for a given cache value.

To accommodate for datatypes that refer to unhashable structures such
as dictionaries, sets and lists, these objects can be made “cacheable”
by assigning hashable structures to the attributes whose names
correspond with the names of the arguments.  For example, a datatype
which accepts a dictionary of lookup values may publish this as a sorted
series of tuples.   Given a previously un-cacheable type as:

```default
class LookupType(UserDefinedType):
    """a custom type that accepts a dictionary as a parameter.

    this is the non-cacheable version, as "self.lookup" is not
    hashable.

    """

    def __init__(self, lookup):
        self.lookup = lookup

    def get_col_spec(self, **kw):
        return "VARCHAR(255)"

    def bind_processor(self, dialect): ...  # works with "self.lookup" ...
```

Where “lookup” is a dictionary.  The type will not be able to generate
a cache key:

```default
>>> type_ = LookupType({"a": 10, "b": 20})
>>> type_._static_cache_key
<stdin>:1: SAWarning: UserDefinedType LookupType({'a': 10, 'b': 20}) will not
produce a cache key because the ``cache_ok`` flag is not set to True.
Set this flag to True if this type object's state is safe to use
in a cache key, or False to disable this warning.
symbol('no_cache')
```

If we **did** set up such a cache key, it wouldn’t be usable. We would
get a tuple structure that contains a dictionary inside of it, which
cannot itself be used as a key in a “cache dictionary” such as SQLAlchemy’s
statement cache, since Python dictionaries aren’t hashable:

```default
>>> # set cache_ok = True
>>> type_.cache_ok = True

>>> # this is the cache key it would generate
>>> key = type_._static_cache_key
>>> key
(<class '__main__.LookupType'>, ('lookup', {'a': 10, 'b': 20}))

>>> # however this key is not hashable, will fail when used with
>>> # SQLAlchemy statement cache
>>> some_cache = {key: "some sql value"}
Traceback (most recent call last): File "<stdin>", line 1,
in <module> TypeError: unhashable type: 'dict'
```

The type may be made cacheable by assigning a sorted tuple of tuples
to the “.lookup” attribute:

```default
class LookupType(UserDefinedType):
    """a custom type that accepts a dictionary as a parameter.

    The dictionary is stored both as itself in a private variable,
    and published in a public variable as a sorted tuple of tuples,
    which is hashable and will also return the same value for any
    two equivalent dictionaries.  Note it assumes the keys and
    values of the dictionary are themselves hashable.

    """

    cache_ok = True

    def __init__(self, lookup):
        self._lookup = lookup

        # assume keys/values of "lookup" are hashable; otherwise
        # they would also need to be converted in some way here
        self.lookup = tuple((key, lookup[key]) for key in sorted(lookup))

    def get_col_spec(self, **kw):
        return "VARCHAR(255)"

    def bind_processor(self, dialect): ...  # works with "self._lookup" ...
```

Where above, the cache key for `LookupType({"a": 10, "b": 20})` will be:

```default
>>> LookupType({"a": 10, "b": 20})._static_cache_key
(<class '__main__.LookupType'>, ('lookup', (('a', 10), ('b', 20))))
```

#### Versionadded
Added in version 1.4.14: - added the `cache_ok` flag to allow
some configurability of caching for `TypeDecorator` classes.

#### Versionadded
Added in version 1.4.28: - added the `ExternalType` mixin which
generalizes the `cache_ok` flag to both the `TypeDecorator`
and `UserDefinedType` classes.

#### SEE ALSO
[SQL Compilation Caching](https://docs.sqlalchemy.org/en/20/core/connections.html#sql-caching)

#### prefix *: [str](https://docs.python.org/3/library/stdtypes.html#str)*

#### \_\_repr_\_() → [str](https://docs.python.org/3/library/stdtypes.html#str)

#### process_bind_param(value, dialect)

This is run when a search query is built or …

#### process_result_value(value, dialect)

convert a raw UUID, without a prefix, to a TypeID with the correct prefix

#### *classmethod* \_\_get_pydantic_core_schema_\_(\_core_schema: pydantic_core.core_schema.CoreSchema, handler: [pydantic.GetJsonSchemaHandler](https://docs.pydantic.dev/latest/api/annotated_handlers/#pydantic.annotated_handlers.GetJsonSchemaHandler)) → pydantic_core.CoreSchema

This fixes the following error: ‘Unable to serialize unknown type’ by telling pydantic how to serialize this field.

Note that TypeIDType MUST be the type of the field in SQLModel otherwise you’ll get serialization errors.
This is done automatically for the mixin but for any relationship fields you’ll need to specify the type explicitly.

- [https://github.com/karma-dev-team/karma-system/blob/ee0c1a06ab2cb7aaca6dc4818312e68c5c623365/app/server/value_objects/steam_id.py#L88](https://github.com/karma-dev-team/karma-system/blob/ee0c1a06ab2cb7aaca6dc4818312e68c5c623365/app/server/value_objects/steam_id.py#L88)
- [https://github.com/hhimanshu/uv-workspaces/blob/main/packages/api/src/_lib/dto/typeid_field.py](https://github.com/hhimanshu/uv-workspaces/blob/main/packages/api/src/_lib/dto/typeid_field.py)
- [https://github.com/karma-dev-team/karma-system/blob/ee0c1a06ab2cb7aaca6dc4818312e68c5c623365/app/base/typeid/type_id.py#L14](https://github.com/karma-dev-team/karma-system/blob/ee0c1a06ab2cb7aaca6dc4818312e68c5c623365/app/base/typeid/type_id.py#L14)
- [https://github.com/pydantic/pydantic/issues/10060](https://github.com/pydantic/pydantic/issues/10060)
- [https://github.com/fastapi/fastapi/discussions/10027](https://github.com/fastapi/fastapi/discussions/10027)
- [https://github.com/alice-biometrics/petisco/blob/b01ef1b84949d156f73919e126ed77aa8e0b48dd/petisco/base/domain/model/uuid.py#L50](https://github.com/alice-biometrics/petisco/blob/b01ef1b84949d156f73919e126ed77aa8e0b48dd/petisco/base/domain/model/uuid.py#L50)

#### *classmethod* \_\_get_pydantic_json_schema_\_(schema: pydantic_core.CoreSchema, handler: [pydantic.GetJsonSchemaHandler](https://docs.pydantic.dev/latest/api/annotated_handlers/#pydantic.annotated_handlers.GetJsonSchemaHandler))

Called when generating the openapi schema. This overrides the function-plain type which
is generated by the no_info_plain_validator_function.

This logic seems to be a hot part of the codebase, so I’d expect this to break as pydantic
fastapi continue to evolve.

Note that this method can return multiple types. A return value can be as simple as:

```pycon
>>> {"type": "string"}
```

Or, you could return a more specific JSON schema type:

```pycon
>>> core_schema.uuid_schema()
```

The problem with using something like uuid_schema is the specific patterns

[https://github.com/BeanieODM/beanie/blob/2190cd9d1fc047af477d5e6897cc283799f54064/beanie/odm/fields.py#L153](https://github.com/BeanieODM/beanie/blob/2190cd9d1fc047af477d5e6897cc283799f54064/beanie/odm/fields.py#L153)
