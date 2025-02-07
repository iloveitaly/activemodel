from sqlmodel.main import FieldInfo


def hash_function_code(func):
    "get sha of a function to easily assert that it hasn't changed"

    import hashlib
    import inspect

    source = inspect.getsource(func)
    return hashlib.sha256(source.encode()).hexdigest()


assert (
    hash_function_code(FieldInfo.__init__)
    == "0d947d2aace56b61b7f7bcbea079488b5fb9a1eb9671536c57b06013799e19b0"
)

original_init = FieldInfo.__init__


def patched_init(self, *args, **kwargs):
    if "sa_column" not in kwargs and "sa_column_kwargs" not in kwargs:
        kwargs["sa_column_kwargs"] = {}

    original_init(self, *args, **kwargs)


FieldInfo.__init__ = patched_init
