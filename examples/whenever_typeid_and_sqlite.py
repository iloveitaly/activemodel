from sqlmodel import SQLModel
from whenever import Instant, PlainDateTime

import activemodel
from activemodel import BaseModel
from activemodel.mixins import TypeIDPrimaryKey
from activemodel.session_manager import get_engine

# Although this looks like it's an absolute path, it is translated into a relative path based on the source location of this file
activemodel.init("sqlite:///database.db")


class User(
    BaseModel,
    # wire this model into the DB, without this alembic will not generate a migration
    table=True,
):
    # you can use a different pk type, but why would you?
    id: str = TypeIDPrimaryKey("user")
    # PlainDateTime matches SQLite behavior: no timezone support
    booked_date: PlainDateTime


# This magic command enables you to avoid the need to run or manage migrations and just magically creates all the tables in the local database
SQLModel.metadata.create_all(get_engine())

# SQLite/stdlib datetimes are microsecond-precision; truncate nanoseconds for a clean round-trip
now_in_sys_time = PlainDateTime(Instant.now().to_system_tz().to_plain().to_stdlib())

user = User(booked_date=now_in_sys_time).save()
fresh_user = User.one(user.id)

assert fresh_user.booked_date == now_in_sys_time
