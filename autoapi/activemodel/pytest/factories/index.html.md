# activemodel.pytest.factories

Notes on polyfactory:

1. is_supported_type validates that the class can be used to generate a factory
[https://github.com/litestar-org/polyfactory/issues/655#issuecomment-2727450854](https://github.com/litestar-org/polyfactory/issues/655#issuecomment-2727450854)

## Classes

| [`SQLModelFactory`](#activemodel.pytest.factories.SQLModelFactory)       | Base factory for SQLModel models:   |
|--------------------------------------------------------------------------|-------------------------------------|
| [`ActiveModelFactory`](#activemodel.pytest.factories.ActiveModelFactory) | Base factory for SQLModel models:   |

## Module Contents

### *class* activemodel.pytest.factories.SQLModelFactory

Bases: `polyfactory.factories.pydantic_factory.ModelFactory`[`T`]

Base factory for SQLModel models:

1. Ability to ignore all relationship fks
2. Option to ignore all pks

#### \_\_is_base_factory_\_ *= True*

Flag dictating whether the factory is a ‘base’ factory. Base factories are registered globally as handlers for types.
For example, the ‘DataclassFactory’, ‘TypedDictFactory’ and ‘ModelFactory’ are all base factories.

#### *classmethod* should_set_field_value(field_meta: polyfactory.field_meta.FieldMeta, \*\*kwargs: Any) → [bool](https://docs.python.org/3/library/functions.html#bool)

Determine whether to set a value for a given field_name.
This is an override of BaseFactory.should_set_field_value.

* **Parameters:**
  * **field_meta** – FieldMeta instance.
  * **kwargs** – Any kwargs passed to the factory.
* **Returns:**
  A boolean determining whether a value should be set for the given field_meta.

### *class* activemodel.pytest.factories.ActiveModelFactory

Bases: [`SQLModelFactory`](#activemodel.pytest.factories.SQLModelFactory)[`T`]

Base factory for SQLModel models:

1. Ability to ignore all relationship fks
2. Option to ignore all pks

#### \_\_is_base_factory_\_ *= True*

Flag dictating whether the factory is a ‘base’ factory. Base factories are registered globally as handlers for types.
For example, the ‘DataclassFactory’, ‘TypedDictFactory’ and ‘ModelFactory’ are all base factories.

#### \_\_sqlalchemy_session_\_ *= None*

#### *classmethod* save(\*args, \*\*kwargs) → [T](../truncate/index.md#activemodel.pytest.truncate.T)

Builds and persists a new model to the database.

Where this gets tricky, is this can be called multiple times within the same callstack. This can happen when
a factory uses other factories to create relationships. This is fine if \_\_sqlalchemy_session_\_ is set, but
if it’s not (in the case of a truncation DB strategy) you’ll run into issues.

In a truncation strategy, the \_\_sqlalchemy_session_\_ is set to None.

#### *classmethod* post_save(model: [T](../truncate/index.md#activemodel.pytest.truncate.T)) → [T](../truncate/index.md#activemodel.pytest.truncate.T)

Post-save hook for performing additional actions after the model has been saved to the database. This is useful
for cases where you need to perform additional operations that require the model be persisted in the database.

The implementation of this method should return a refreshed instance of the model if that’s necessary. For
example, if your post_save hook triggers another factory save(), the current model will likely be expired
and detached, leading to a DetachedInstanceError when accessing it later.

To avoid this, return model.refresh() at the end of your implementation.

#### *classmethod* foreign_key_typeid()

Return a random type id for the foreign key on this model.

This is helpful for generating TypeIDs for testing 404s, parsing, manually settings, etc

#### *classmethod* should_set_field_value(field_meta: polyfactory.field_meta.FieldMeta, \*\*kwargs: Any) → [bool](https://docs.python.org/3/library/functions.html#bool)

Determine whether to set a value for a given field_name.
This is an override of BaseFactory.should_set_field_value.

* **Parameters:**
  * **field_meta** – FieldMeta instance.
  * **kwargs** – Any kwargs passed to the factory.
* **Returns:**
  A boolean determining whether a value should be set for the given field_meta.
