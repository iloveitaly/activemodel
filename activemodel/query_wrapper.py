from typing import Generic, TypeVar

from sqlmodel.sql.expression import SelectOfScalar

WrappedModelType = TypeVar("WrappedModelType")


def compile_sql(target: SelectOfScalar):
    return str(target.compile(get_engine().connect()))


class QueryWrapper(Generic[WrappedModelType]):
    """
    Make it easy to run queries off of a model
    """

    def __init__(self, cls, *args) -> None:
        # TODO add generics here
        # self.target: SelectOfScalar[T] = sql.select(cls)

        if args:
            # very naive, let's assume the args are specific select statements
            self.target = sql.select(*args).select_from(cls)
        else:
            self.target = sql.select(cls)

    # TODO the .exec results should be handled in one shot

    def first(self):
        with get_session() as session:
            return session.exec(self.target).first()

    def one(self):
        with get_session() as session:
            return session.exec(self.target).one()

    def all(self):
        with get_session() as session:
            result = session.exec(self.target)
            for row in result:
                yield row

    def exec(self):
        # TODO do we really need a unique session each time?
        with get_session() as session:
            return session.exec(self.target)

    def delete(self):
        with get_session() as session:
            session.delete(self.target)

    def __getattr__(self, name):
        """
        This is called to retrieve the function to execute
        """

        # TODO prefer methods defined in this class
        if not hasattr(self.target, name):
            return super().__getattribute__(name)

        attr = getattr(self.target, name)

        if callable(attr):

            def wrapper(*args, **kwargs):
                result = attr(*args, **kwargs)
                self.target = result
                return self

            return wrapper

        # If the attribute or method is not defined in this class,
        # delegate the call to the `target` object
        return getattr(self.target, name)

    def sql(self):
        """
        Output the raw SQL of the query
        """

        return compile_sql(self.target)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}: Current SQL:\n{self.sql()}"
