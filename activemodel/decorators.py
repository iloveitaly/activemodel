from pydantic import computed_field


def property_field(func=None, /, **kwargs):
    """`@property` enables attribute-style access; `@computed_field` includes the field in pydantic serialization."""

    def wrap(f):
        return computed_field(**kwargs)(property(f))

    if func is None:
        return wrap
    return wrap(func)
