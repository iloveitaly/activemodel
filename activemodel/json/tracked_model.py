"""
Field access and mutation tracking for Pydantic models, to eliminate manual flag_modified
calls on JSONB columns. Inspect mutated_fields to know exactly which columns are dirty.

The complementary approach in tracked_pydantic.py wires this more tightly to SQLAlchemy:
a __class__ swap to a cached dynamic subclass with weakrefs to the ORM parent calls
sa_flag_modified automatically on any public field mutation.

https://grok.com/share/bGVnYWN5_3b01c1e5-2e00-4e04-b57c-6ad0fd993677
"""

from pydantic import BaseModel, ConfigDict, computed_field
from typing import Any, Set


class TrackingModel(BaseModel):
    # extra="allow" lets callers attach arbitrary keys without declaring them as model fields.
    model_config = ConfigDict(extra="allow")

    def __init__(self, **data: Any) -> None:
        # object.__setattr__ bypasses Pydantic's __setattr__ so we can set private tracking
        # state before super().__init__ triggers field assignment and our own __setattr__.
        object.__setattr__(self, "_initializing", True)
        super().__init__(**data)
        object.__setattr__(self, "_accessed", set())
        object.__setattr__(self, "_mutated", set())
        object.__setattr__(self, "_initializing", False)

    def __getattribute__(self, name: str) -> Any:
        # Short-circuit for private/dunder names and our own computed properties to avoid
        # infinite recursion — __getattribute__ is called for every attribute lookup.
        if name.startswith("_") or name in (
            "model_fields",
            "__pydantic_extra__",
            "accessed_fields",
            "never_accessed_fields",
            "mutated_fields",
        ):
            return object.__getattribute__(self, name)
        try:
            value = object.__getattribute__(self, name)
        except AttributeError:
            # Extra fields (model_config extra="allow") are stored in __pydantic_extra__,
            # not on the instance directly, so we check there before re-raising.
            if self.__pydantic_extra__ is not None and name in self.__pydantic_extra__:
                self._accessed.add(name)
                return self.__pydantic_extra__[name]
            raise
        else:
            if self.model_fields.get(name) is not None:
                self._accessed.add(name)
            return value

    def __setattr__(self, name: str, value: Any) -> None:
        # Suppress mutation tracking during __init__ so field initialization isn't recorded.
        if self._initializing:
            return super().__setattr__(name, value)
        self._mutated.add(name)
        super().__setattr__(name, value)

    # computed_field(exclude=True) exposes the property via the model API but omits it from
    # model_dump() / model_dump_json() so tracking state never leaks into serialized output.

    @computed_field(exclude=True)
    @property
    def accessed_fields(self) -> Set[str]:
        return self._accessed

    @computed_field(exclude=True)
    @property
    def never_accessed_fields(self) -> Set[str]:
        # Union of declared fields and any extra fields set at runtime.
        fields = set(self.model_fields)
        if self.__pydantic_extra__:
            fields |= set(self.__pydantic_extra__)
        return fields - self._accessed

    @computed_field(exclude=True)
    @property
    def mutated_fields(self) -> Set[str]:
        return self._mutated
