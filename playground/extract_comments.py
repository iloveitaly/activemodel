import sqlalchemy as sa
from sqlmodel import SQLModel, create_engine, Session


def extract_comments(engine):
    comments = {}
    # Reflect all tables if needed; otherwise, rely on model metadata
    for model in SQLModel.__subclasses__():
        table = model.__table__
        # Retrieve table-level comment
        table_comment = table.comment
        # Retrieve comments for each column
        column_comments = {
            col.name: col.comment for col in table.columns if col.comment
        }
        comments[table.name] = {
            "table_comment": table_comment,
            "column_comments": column_comments,
        }
    return comments


if __name__ == "__main__":
    # Adjust your connection string accordingly
    engine = create_engine("sqlite:///database.db")
    with Session(engine) as session:
        comments = extract_comments(engine)
        for table, data in comments.items():
            print(f"Table: {table}")
            print(f" - Table Comment: {data['table_comment']}")
            print(" - Column Comments:")
            for col, comment in data["column_comments"].items():
                print(f"    {col}: {comment}")
