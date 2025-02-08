"""
Note that FieldInfo *from pydantic* is used when a "bare" field is defined. This can be confusing, because when inspecting model fields, the class name looks exactly the same.

In that case, this patch does not do a thing.
"""

from pydantic_core import PydanticUndefined
from sqlmodel.main import FieldInfo


def hash_function_code(func):
    "get sha of a function to easily assert that it hasn't changed"

    import hashlib
    import inspect

    source = inspect.getsource(func)
    return hashlib.sha256(source.encode()).hexdigest()


# assert (
#     hash_function_code(FieldInfo.__init__)
#     == "0d947d2aace56b61b7f7bcbea079488b5fb9a1eb9671536c57b06013799e19b0"
# )

original_init = FieldInfo.__init__


def patched_init(self, *args, **kwargs):
    if (
        kwargs["sa_column"] == PydanticUndefined
        and kwargs["sa_column_kwargs"] == PydanticUndefined
    ):
        kwargs["sa_column_kwargs"] = {}
    # else:
    #     breakpoint()

    original_init(self, *args, **kwargs)


FieldInfo.__init__ = patched_init
