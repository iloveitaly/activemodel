# activemodel.types.whenever

## Submodules

* [activemodel.types.whenever.instant_type](instant_type/index.md)
* [activemodel.types.whenever.plain_date_time_type](plain_date_time_type/index.md)
* [activemodel.types.whenever.zoned_date_time_type](zoned_date_time_type/index.md)

## Classes

| [`InstantType`](#activemodel.types.whenever.InstantType)             | SQLAlchemy TypeDecorator for whenever.Instant.       |
|----------------------------------------------------------------------|------------------------------------------------------|
| [`PlainDateTimeType`](#activemodel.types.whenever.PlainDateTimeType) | SQLAlchemy TypeDecorator for whenever.PlainDateTime. |
| [`ZonedDateTimeType`](#activemodel.types.whenever.ZonedDateTimeType) | SQLAlchemy TypeDecorator for whenever.ZonedDateTime. |

## Package Contents

### *class* activemodel.types.whenever.InstantType(\*args: Any, \*\*kwargs: Any)

Bases: [`sqlalchemy.types.TypeDecorator`](https://docs.sqlalchemy.org/en/20/core/custom_types.html#sqlalchemy.types.TypeDecorator)

SQLAlchemy TypeDecorator for whenever.Instant.

Stores as a timezone-aware datetime in the database (UTC).
Reconstructs as an Instant on read.

Usage:
: created_at: Instant | None = None

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

#### process_bind_param(value, dialect)

Receive a bound parameter value to be converted.

Custom subclasses of `_types.TypeDecorator` should override
this method to provide custom behaviors for incoming data values.
This method is called at **statement execution time** and is passed
the literal Python data value which is to be associated with a bound
parameter in the statement.

The operation could be anything desired to perform custom
behavior, such as transforming or serializing data.
This could also be used as a hook for validating logic.

* **Parameters:**
  * **value** – Data to operate upon, of any type expected by
    this method in the subclass.  Can be `None`.
  * **dialect** – the `Dialect` in use.

#### SEE ALSO
[Augmenting Existing Types](https://docs.sqlalchemy.org/en/20/core/custom_types.html#types-typedecorator)

`_types.TypeDecorator.process_result_value()`

#### process_result_value(value, dialect)

Receive a result-row column value to be converted.

Custom subclasses of `_types.TypeDecorator` should override
this method to provide custom behaviors for data values
being received in result rows coming from the database.
This method is called at **result fetching time** and is passed
the literal Python data value that’s extracted from a database result
row.

The operation could be anything desired to perform custom
behavior, such as transforming or deserializing data.

* **Parameters:**
  * **value** – Data to operate upon, of any type expected by
    this method in the subclass.  Can be `None`.
  * **dialect** – the `Dialect` in use.

#### SEE ALSO
[Augmenting Existing Types](https://docs.sqlalchemy.org/en/20/core/custom_types.html#types-typedecorator)

`_types.TypeDecorator.process_bind_param()`

#### *classmethod* \_\_get_pydantic_core_schema_\_(\_source_type: [object](https://docs.python.org/3/library/functions.html#object), handler: [pydantic.GetJsonSchemaHandler](https://pydantic.dev/docs/validation/latest/api/pydantic/annotated_handlers/#pydantic.annotated_handlers.GetJsonSchemaHandler)) → pydantic_core.CoreSchema

#### *classmethod* \_\_get_pydantic_json_schema_\_(schema: pydantic_core.CoreSchema, handler: [pydantic.GetJsonSchemaHandler](https://pydantic.dev/docs/validation/latest/api/pydantic/annotated_handlers/#pydantic.annotated_handlers.GetJsonSchemaHandler))

### *class* activemodel.types.whenever.PlainDateTimeType(\*args: Any, \*\*kwargs: Any)

Bases: [`sqlalchemy.types.TypeDecorator`](https://docs.sqlalchemy.org/en/20/core/custom_types.html#sqlalchemy.types.TypeDecorator)

SQLAlchemy TypeDecorator for whenever.PlainDateTime.

Stores as a naive datetime in the database.
Reconstructs as a PlainDateTime on read.

This is useful for SQLite and other databases that do not have robust
timezone-aware datetime support, or for fields that are intentionally meant
to represent a local wall-clock time without timezone information.

Usage:
: local_time: PlainDateTime | None = None

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

#### process_bind_param(value, dialect)

Receive a bound parameter value to be converted.

Custom subclasses of `_types.TypeDecorator` should override
this method to provide custom behaviors for incoming data values.
This method is called at **statement execution time** and is passed
the literal Python data value which is to be associated with a bound
parameter in the statement.

The operation could be anything desired to perform custom
behavior, such as transforming or serializing data.
This could also be used as a hook for validating logic.

* **Parameters:**
  * **value** – Data to operate upon, of any type expected by
    this method in the subclass.  Can be `None`.
  * **dialect** – the `Dialect` in use.

#### SEE ALSO
[Augmenting Existing Types](https://docs.sqlalchemy.org/en/20/core/custom_types.html#types-typedecorator)

`_types.TypeDecorator.process_result_value()`

#### process_result_value(value, dialect)

Receive a result-row column value to be converted.

Custom subclasses of `_types.TypeDecorator` should override
this method to provide custom behaviors for data values
being received in result rows coming from the database.
This method is called at **result fetching time** and is passed
the literal Python data value that’s extracted from a database result
row.

The operation could be anything desired to perform custom
behavior, such as transforming or deserializing data.

* **Parameters:**
  * **value** – Data to operate upon, of any type expected by
    this method in the subclass.  Can be `None`.
  * **dialect** – the `Dialect` in use.

#### SEE ALSO
[Augmenting Existing Types](https://docs.sqlalchemy.org/en/20/core/custom_types.html#types-typedecorator)

`_types.TypeDecorator.process_bind_param()`

#### *classmethod* \_\_get_pydantic_core_schema_\_(\_source_type: [object](https://docs.python.org/3/library/functions.html#object), handler: [pydantic.GetJsonSchemaHandler](https://pydantic.dev/docs/validation/latest/api/pydantic/annotated_handlers/#pydantic.annotated_handlers.GetJsonSchemaHandler)) → pydantic_core.CoreSchema

#### *classmethod* \_\_get_pydantic_json_schema_\_(schema: pydantic_core.CoreSchema, handler: [pydantic.GetJsonSchemaHandler](https://pydantic.dev/docs/validation/latest/api/pydantic/annotated_handlers/#pydantic.annotated_handlers.GetJsonSchemaHandler))

### *class* activemodel.types.whenever.ZonedDateTimeType(\*args: Any, \*\*kwargs: Any)

Bases: [`sqlalchemy.types.TypeDecorator`](https://docs.sqlalchemy.org/en/20/core/custom_types.html#sqlalchemy.types.TypeDecorator)

SQLAlchemy TypeDecorator for whenever.ZonedDateTime.

Stores as a timezone-aware datetime in the database. Note that the IANA
timezone name is not preserved — the DB stores the UTC offset at the time
of writing. On read, the value is reconstructed as a ZonedDateTime, but
the timezone will be a fixed-offset zone rather than the original IANA name.

Usage:
: scheduled_at: ZonedDateTime | None = None

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

#### process_bind_param(value, dialect)

Receive a bound parameter value to be converted.

Custom subclasses of `_types.TypeDecorator` should override
this method to provide custom behaviors for incoming data values.
This method is called at **statement execution time** and is passed
the literal Python data value which is to be associated with a bound
parameter in the statement.

The operation could be anything desired to perform custom
behavior, such as transforming or serializing data.
This could also be used as a hook for validating logic.

* **Parameters:**
  * **value** – Data to operate upon, of any type expected by
    this method in the subclass.  Can be `None`.
  * **dialect** – the `Dialect` in use.

#### SEE ALSO
[Augmenting Existing Types](https://docs.sqlalchemy.org/en/20/core/custom_types.html#types-typedecorator)

`_types.TypeDecorator.process_result_value()`

#### process_result_value(value, dialect)

Receive a result-row column value to be converted.

Custom subclasses of `_types.TypeDecorator` should override
this method to provide custom behaviors for data values
being received in result rows coming from the database.
This method is called at **result fetching time** and is passed
the literal Python data value that’s extracted from a database result
row.

The operation could be anything desired to perform custom
behavior, such as transforming or deserializing data.

* **Parameters:**
  * **value** – Data to operate upon, of any type expected by
    this method in the subclass.  Can be `None`.
  * **dialect** – the `Dialect` in use.

#### SEE ALSO
[Augmenting Existing Types](https://docs.sqlalchemy.org/en/20/core/custom_types.html#types-typedecorator)

`_types.TypeDecorator.process_bind_param()`

#### *classmethod* \_\_get_pydantic_core_schema_\_(\_source_type: [object](https://docs.python.org/3/library/functions.html#object), handler: [pydantic.GetJsonSchemaHandler](https://pydantic.dev/docs/validation/latest/api/pydantic/annotated_handlers/#pydantic.annotated_handlers.GetJsonSchemaHandler)) → pydantic_core.CoreSchema

#### *classmethod* \_\_get_pydantic_json_schema_\_(schema: pydantic_core.CoreSchema, handler: [pydantic.GetJsonSchemaHandler](https://pydantic.dev/docs/validation/latest/api/pydantic/annotated_handlers/#pydantic.annotated_handlers.GetJsonSchemaHandler))
