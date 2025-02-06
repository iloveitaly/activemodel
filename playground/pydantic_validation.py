# TODO this does not seem to work with the latest 2.9.x pydantic and sqlmodel, should investigate further
# https://github.com/SE-Sustainability-OSS/ecodev-core/blob/main/ecodev_core/sqlmodel_utils.py
class SQLModelWithValidation(SQLModel):
    """
    Helper class to ease validation in SQLModel classes with table=True
    """

    @classmethod
    def create(cls, **kwargs):
        """
        Forces validation to take place, even for SQLModel classes with table=True
        """
        return cls(**cls.__bases__[0](**kwargs).model_dump())
