"""
Do not import unless you have Celery/Kombu installed.

In order for TypeID objects to be properly handled by celery, a custom encoder must be registered.
"""

from kombu.utils.json import register_type
from typeid import TypeID


def register_celery_typeid_encoder():
    "this ensures TypeID objects passed as arguments to a delayed function are properly serialized"

    def class_full_name(clz) -> str:
        return ".".join([clz.__module__, clz.__qualname__])

    def _encoder(obj: TypeID) -> str:
        return str(obj)

    def _decoder(data: str) -> TypeID:
        return TypeID.from_string(data)

    register_type(
        TypeID,
        class_full_name(TypeID),
        encoder=_encoder,
        decoder=_decoder,
    )
