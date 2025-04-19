from sqlalchemy import text
from sqlmodel.sql.expression import SelectOfScalar

from .session_manager import get_engine, get_session


def compile_sql(target: SelectOfScalar) -> str:
    "convert a query into SQL, helpful for debugging sqlalchemy/sqlmodel queries"

    dialect = get_engine().dialect
    # TODO I wonder if we could store the dialect to avoid getting an engine reference
    compiled = target.compile(dialect=dialect, compile_kwargs={"literal_binds": True})
    return str(compiled)


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
