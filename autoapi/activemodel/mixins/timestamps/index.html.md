# activemodel.mixins.timestamps

## Classes

| [`TimestampsMixin`](#activemodel.mixins.timestamps.TimestampsMixin)   | Simple created at and updated at timestamps. Mix them into your model:   |
|-----------------------------------------------------------------------|--------------------------------------------------------------------------|

## Module Contents

### *class* activemodel.mixins.timestamps.TimestampsMixin

Simple created at and updated at timestamps. Mix them into your model:

```pycon
>>> class MyModel(TimestampsMixin, SQLModel):
>>>    pass
```

Notes:

- Originally pulled from: [https://github.com/tiangolo/sqlmodel/issues/252](https://github.com/tiangolo/sqlmodel/issues/252)
- Related issue: [https://github.com/fastapi/sqlmodel/issues/539](https://github.com/fastapi/sqlmodel/issues/539)

#### created_at *: [datetime.datetime](https://docs.python.org/3/library/datetime.html#datetime.datetime) | [None](https://docs.python.org/3/library/constants.html#None)* *= None*

#### updated_at *: [datetime.datetime](https://docs.python.org/3/library/datetime.html#datetime.datetime) | [None](https://docs.python.org/3/library/constants.html#None)* *= None*
