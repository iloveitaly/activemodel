import sqlmodel as sm
from sqlmodel.sql.expression import SelectOfScalar
from typing import overload, Literal

from activemodel.types.sqlalchemy_protocol import SQLAlchemyQueryMethods

from .session_manager import get_session
from .utils import compile_sql


class QueryWrapper[T: sm.SQLModel](SQLAlchemyQueryMethods[T]):
    """
    Make it easy to run queries off of a model
    """

    target: SelectOfScalar[T]

    def __init__(self, cls: T, *args) -> None:
        # TODO add generics here
        # self.target: SelectOfScalar[T] = sql.select(cls)

        if args:
            # very naive, let's assume the args are specific select statements
            self.target = sm.select(*args).select_from(cls)
        else:
            self.target = sm.select(cls)

    # TODO the .exec results should be handled in one shot

    def first(self):
        with get_session() as session:
            return session.exec(self.target).first()

    def one(self):
        "requires exactly one result in the dataset"
        with get_session() as session:
            return session.exec(self.target).one()

    def all(self):
        with get_session() as session:
            result = session.exec(self.target)
            for row in result:
                yield row

    def count(self):
        """
        I did some basic tests
        """
        with get_session() as session:
            return session.scalar(sm.select(sm.func.count()).select_from(self.target))

    # TODO typing is broken here
    # TODO would be great to define a default return type if nothing is found
    def scalar(self):
        """
        >>>
        """
        with get_session() as session:
            return session.scalar(self.target)

    def exec(self):
        with get_session() as session:
            return session.exec(self.target)

    def delete(self):
        with get_session() as session:
            return session.delete(self.target)

    def exists(self) -> bool:
        """Return True if the current query yields at least one row.

        Uses the SQLAlchemy exists() construct against a LIMIT 1 version of
        the current target for efficiency. Keeps the original target intact.
        """
        with get_session() as session:
            exists_stmt = sm.select(sm.exists(self.target))
            result = session.scalar(exists_stmt)
            return bool(result)

    def __getattr__(self, name):
        """
        This implements the magic that forwards function calls to sqlalchemy.
        """

        # TODO prefer methods defined in this class

        if not hasattr(self.target, name):
            return super().__getattribute__(name)

        sqlalchemy_target = getattr(self.target, name)

        if callable(sqlalchemy_target):

            def wrapper(*args, **kwargs):
                result = sqlalchemy_target(*args, **kwargs)
                self.target = result  # type: ignore[assignment]
                return self

            return wrapper

        # If the attribute or method is not defined in this class,
        # delegate the call to the `target` object
        return getattr(self.target, name)

    def sql(self):
        """
        Output the raw SQL of the query for debugging
        """

        return compile_sql(self.target)

    @overload
    def sample(self) -> T | None: ...

    @overload
    def sample(self, n: Literal[1]) -> T | None: ...

    @overload
    def sample(self, n: int) -> list[T]: ...

    def sample(self, n: int = 1) -> T | None | list[T]:
        """Return a random sample of rows from the current query.

        Parameters
        ----------
        n: int
            Number of rows to return. Defaults to 1.

        Behavior
        --------
        - Returns a single model instance when ``n == 1`` (or ``None`` if no rows)
        - Returns a list[Model] when ``n > 1`` (possibly empty list when no rows)
        - Sampling is performed by appending an ``ORDER BY RANDOM()`` / ``func.random()``
          and ``LIMIT n`` clause to the existing query target.
        - Keeps original query intact (does not mutate ``self.target``) so further
          chaining works as expected.
        """

        if n < 1:
            raise ValueError("n must be >= 1")

        # Build a new randomized limited query leaving self.target untouched
        randomized = self.target.order_by(sm.func.random()).limit(n)

        with get_session() as session:
            result = list(session.exec(randomized))

        if n == 1:
            # Return the single instance or None
            return result[0] if result else None

        return result

    def __repr__(self) -> str:
        # TODO we should improve structure of this a bit more, maybe wrap in <> or something?
        return f"{self.__class__.__name__}: Current SQL:\n{self.sql()}"
