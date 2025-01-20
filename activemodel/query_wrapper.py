import sqlmodel as sm
from sqlmodel.sql.expression import SelectOfScalar

from .session_manager import get_session
from .utils import compile_sql


class QueryWrapper[T: sm.SQLModel]:
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

    def exec(self):
        with get_session() as session:
            return session.exec(self.target)

    def delete(self):
        with get_session() as session:
            session.delete(self.target)

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
                self.target = result
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

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}: Current SQL:\n{self.sql()}"
