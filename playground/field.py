from sqlmodel import Field as SQLModelField


class Field(SQLModelField):
    def __init__(self, *args, **kwargs):
        if "description" in kwargs:
            description = kwargs.get("description")
            if "sa_column_kwargs" in kwargs:
                sa_column_kwargs = kwargs.get("sa_column_kwargs")
                sa_column_kwargs["comment"] = description
            else:
                kwargs["sa_column_kwargs"] = {"comment": description}
        super().__init__(*args, **kwargs)
