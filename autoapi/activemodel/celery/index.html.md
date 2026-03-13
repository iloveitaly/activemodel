# activemodel.celery

Do not import unless you have Celery/Kombu installed.

In order for TypeID objects to be properly handled by celery, a custom encoder must be registered.

## Functions

| [`register_celery_typeid_encoder`](#activemodel.celery.register_celery_typeid_encoder)()   | Ensures TypeID objects passed as arguments to a delayed function are properly serialized.   |
|--------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------|

## Module Contents

### activemodel.celery.register_celery_typeid_encoder()

Ensures TypeID objects passed as arguments to a delayed function are properly serialized.

Run at the top of your celery initialization script.
