from sqlmodel.sql.expression import SelectOfScalar

from activemodel import get_engine


def compile_sql(target: SelectOfScalar):
    dialect = get_engine().dialect
    # TODO I wonder if we could store the dialect to avoid getting an engine reference
    compiled = target.compile(dialect=dialect, compile_kwargs={"literal_binds": True})
    return str(compiled)


def raw_sql_exec(raw_query: str):
    with get_session() as session:
        session.execute(text(raw_query))
