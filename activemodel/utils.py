import re

from sqlalchemy import text
from sqlmodel.sql.expression import SelectOfScalar

from .session_manager import get_engine, get_session


def to_snake_case(name: str) -> str:
    """
    Converts a PascalCase or camelCase string to snake_case.
    Properly handles acronyms like 'LLMCache' -> 'llm_cache'.

    Source: https://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-snake-case
    """
    s1 = re.sub(r"(?<!^)(?<!_)([A-Z][a-z]+)", r"_\1", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def compile_sql(target: SelectOfScalar) -> str:
    "convert a query into SQL, helpful for debugging sqlalchemy/sqlmodel queries"

    dialect = get_engine().dialect
    # TODO I wonder if we could store the dialect to avoid getting an engine reference
    compiled = target.compile(dialect=dialect, compile_kwargs={"literal_binds": True})
    return str(compiled)


# alternative implementation we could consider
# def select(cls):
#     with get_session() as session:
#         results = session.exec(sql.select(cls))
#         for result in results:
#             yield result


# TODO wait so why isn't this typed?
# TODO document further, lots of risks here
def raw_sql_exec(raw_query: str):
    """
    https://github.com/tiangolo/sqlmodel/discussions/772
    """
    with get_session() as session:
        session.execute(text(raw_query))


def hash_function_code(func):
    "get sha of a function to easily assert that it hasn't changed"

    import hashlib
    import inspect

    source = inspect.getsource(func)
    return hashlib.sha256(source.encode()).hexdigest()


def is_database_empty(exclude: list[type] | None = None) -> bool:
    """
    Check if any table in the database has records using Model.count().

    Useful for detecting an empty database state to run operations such as seeding, etc.
    """

    from .base_model import BaseModel
    from .logger import logger

    if exclude is None:
        exclude = []

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
