from sqlalchemy import text
from sqlmodel.sql.expression import SelectOfScalar

from .session_manager import get_engine, get_session


def compile_sql(target: SelectOfScalar) -> str:
    "convert a query into SQL, helpful for debugging sqlalchemy/sqlmodel queries"

    dialect = get_engine().dialect
    # TODO I wonder if we could store the dialect to avoid getting an engine reference
    compiled = target.compile(dialect=dialect, compile_kwargs={"literal_binds": True})
    return str(compiled)


# TODO wait so why isn't this typed?
# TODO document further, lots of risks here
def raw_sql_exec(raw_query: str):
    with get_session() as session:
        session.execute(text(raw_query))


def hash_function_code(func):
    "get sha of a function to easily assert that it hasn't changed"

    import hashlib
    import inspect

    source = inspect.getsource(func)
    return hashlib.sha256(source.encode()).hexdigest()


def is_database_empty(exclude: list[type] = []) -> bool:
    """
    Check if any table in the database has records using Model.count().

    Useful for detecting an empty database state to run operations such as seeding, etc.
    """

    from .base_model import BaseModel
    from .logger import logger

    # Get all subclasses recursively
    all_models = BaseModel.__subclasses__()
    for model in all_models:
        all_models.extend(model.__subclasses__())

    # filter to only unique classes
    all_models = list(set(all_models))

    for model_cls in all_models:
        if model_cls in exclude:
            table_name = getattr(model_cls, "__tablename__", model_cls.__name__)
            logger.info(f"skipping table in empty check: {table_name}")
            continue

        # only check models that are actually tables
        if not model_cls.model_config.get("table"):
            continue

        count = model_cls.count()
        if count > 0:
            logger.warning(
                f"table is not empty: {model_cls.__tablename__} (count={count})"
            )
            return False

    return True
